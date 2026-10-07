"""Celery ingestion worker tasks with atomic version activation and lease management."""
from datetime import datetime, timezone, timedelta
import logging
import os
from pathlib import Path
from uuid import UUID
from celery.exceptions import MaxRetriesExceededError
from sqlalchemy import select, delete

from app.database.session import SessionLocal
from app.database.models import (
    CanonicalRecord,
    ImportJob,
    ParseRun,
    Source,
    SourceVersion,
    utcnow,
)
from app.rag.contracts import SourceLocator
from app.rag.parsers.base import (
    MalformedSourceError,
    ParserDiagnostic,
    UnsupportedFormatError,
)
from app.rag.parsers.docling_adapter import DoclingAdapter
from app.rag.parsers.profiles import validate_records, validate_document_profile
from app.rag.parsers.spreadsheet import SpreadsheetParser
from app.rag.parsers.structured import StructuredParser
from app.rag.parsers.text_log import TextLogParser
from app.workers.celery_app import celery_app

logger = logging.getLogger("rag.worker")


def get_source_storage_path(storage_key: str) -> Path:
    """Trả về đường dẫn an toàn tới tệp nguồn trong storage riêng tư."""
    default_dir = "/tmp/storage" if os.environ.get("TEST_MODE") == "true" else "/app/storage"
    storage_dir = os.environ.get("STORAGE_DIR", default_dir)
    return Path(storage_dir) / "sources" / storage_key


@celery_app.task(bind=True, max_retries=3)
def process_ingestion_job(self, job_id_str: str) -> None:
    """Tác vụ xử lý nạp dữ liệu và kích hoạt phiên bản nguồn nguyên tử."""
    try:
        job_uuid = UUID(job_id_str)
    except (ValueError, TypeError):
        logger.error("Mã job_id_str không hợp lệ: %s", job_id_str)
        return

    with SessionLocal() as db:
        job = db.get(ImportJob, job_uuid)
        if not job:
            logger.warning("Không tìm thấy ImportJob có ID: %s", job_id_str)
            return

        version = db.get(SourceVersion, job.source_version_id)
        if not version:
            job.state = "failed"
            job.error_code = "VERSION_NOT_FOUND"
            job.error_message = f"Không tìm thấy SourceVersion ID {job.source_version_id}"
            db.commit()
            return

        source = db.get(Source, version.source_id)
        if not source:
            job.state = "failed"
            job.error_code = "SOURCE_NOT_FOUND"
            job.error_message = f"Không tìm thấy Source ID {version.source_id}"
            db.commit()
            return

        # Fencing / Tombstone check
        if source.deleted_at is not None:
            job.state = "failed"
            job.error_code = "SOURCE_DELETED"
            job.error_message = "Nguồn đã bị xóa"
            job.lease_expires_at = None
            db.commit()
            logger.info("Dừng xử lý job %s do Source %s đã bị xóa (tombstone)", job_id_str, source.id)
            return

        # Acquire worker lease
        job.state = "processing"
        job.lease_expires_at = utcnow() + timedelta(minutes=10)
        job.attempt_count += 1
        db.commit()

        # Đọc dữ liệu từ private storage
        storage_path = get_source_storage_path(version.storage_key)
        try:
            content_bytes = storage_path.read_bytes()
        except Exception as exc:
            logger.exception("Lỗi I/O đọc tệp tại %s: %s", storage_path, exc)
            retries = getattr(self.request, "retries", 0) if hasattr(self, "request") else 0
            max_r = getattr(self, "max_retries", 3)
            if retries >= max_r:
                job.state = "failed"
                job.error_code = "FILE_READ_ERROR"
                job.error_message = f"Không thể đọc tệp từ private storage: {exc}"
                job.lease_expires_at = None
                db.commit()
                return
            else:
                db.commit()
                raise self.retry(exc=exc, countdown=2 ** retries)

        # Chọn parser adapter tương ứng
        ext = Path(source.logical_filename).suffix.lower()
        locator_base = SourceLocator(
            source_id=source.id,
            source_version=version.version_number,
        )

        try:
            if ext in (".pdf", ".docx"):
                parser = DoclingAdapter()
                parse_result = parser.parse_bytes(
                    content_bytes,
                    locator_base,
                    source.dataset_id,
                    file_name=source.logical_filename,
                )
            elif ext in (".xlsx", ".csv"):
                parser = SpreadsheetParser()
                parse_result = parser.parse_bytes(content_bytes, locator_base, source.dataset_id)
            elif ext in (".json", ".jsonl"):
                parser = StructuredParser()
                parse_result = parser.parse_bytes(content_bytes, locator_base, source.dataset_id)
            elif ext in (".txt", ".log"):
                parser = TextLogParser()
                parse_result = parser.parse_bytes(content_bytes, locator_base, source.dataset_id)
            else:
                raise UnsupportedFormatError(f"Định dạng tệp không được hỗ trợ: '{ext}'")

            # Chuẩn hóa và kiểm tra schema theo source.profile_id
            if source.profile_id == "document":
                full_text = " ".join(r.text for r in parse_result.records)
                doc_val = validate_document_profile(full_text)
                is_valid = doc_val.is_valid
                diagnostics = tuple(doc_val.diagnostics)
                normalized_list = [r.metadata for r in parse_result.records]
            else:
                raw_records = [r.metadata for r in parse_result.records]
                if not raw_records:
                    is_valid = False
                    diagnostics = (
                        ParserDiagnostic(row=1, field="data", reason="Tệp không chứa bản ghi dữ liệu nào"),
                    )
                    normalized_list = []
                else:
                    normalized_list, diagnostics, is_valid = validate_records(source.profile_id, raw_records)

            # Quy tắc thất bại nguyên tử (Atomic Failure Guarantee - D-02, D-04)
            if not is_valid or diagnostics:
                job.state = "failed"
                job.error_code = "SCHEMA_VALIDATION_ERROR"
                job.error_message = f"Xác thực lược đồ thất bại ({len(diagnostics)} lỗi)"
                job.diagnostics = {
                    "errors": [
                        d.model_dump(mode="json", exclude_none=True) if hasattr(d, "model_dump") else d
                        for d in diagnostics
                    ]
                }
                job.lease_expires_at = None
                # TUYỆT ĐỐI KHÔNG cập nhật source.active_version_id
                db.commit()
                return

            # Quy tắc kích hoạt nguyên tử (Atomic Activation Guarantee - D-02)
            # Khóa bản ghi Source với with_for_update() và kiểm tra lại fencing
            source_locked = db.scalars(
                select(Source).where(Source.id == source.id).with_for_update()
            ).first()

            if not source_locked or source_locked.deleted_at is not None:
                job.state = "failed"
                job.error_code = "SOURCE_DELETED"
                job.error_message = "Nguồn đã bị xóa"
                job.lease_expires_at = None
                db.commit()
                return

            # Dọn dẹp dữ liệu cũ của job này (đảm bảo idempotent khi retry)
            existing_runs = db.scalars(select(ParseRun).where(ParseRun.job_id == job.id)).all()
            for erun in existing_runs:
                db.execute(delete(CanonicalRecord).where(CanonicalRecord.parse_run_id == erun.id))
                db.delete(erun)
            db.flush()

            # Tạo bản ghi ParseRun đã xuất bản
            parse_run = ParseRun(
                source_version_id=version.id,
                job_id=job.id,
                parser_name=parser.__class__.__name__,
                parser_version="1.0.0",
                status="published",
            )
            db.add(parse_run)
            db.flush()

            # Lưu canonical_records
            for idx, prec in enumerate(parse_result.records):
                meta = normalized_list[idx] if idx < len(normalized_list) else prec.metadata
                record = CanonicalRecord(
                    parse_run_id=parse_run.id,
                    source_version_id=version.id,
                    dataset_id=source.dataset_id,
                    position=prec.position,
                    locator_data=prec.locator.model_dump(mode="json", exclude_none=True),
                    content_text=prec.text,
                    record_metadata=meta,
                )
                db.add(record)

            # Kích hoạt phiên bản và hoàn tất job
            source.active_version_id = version.id
            job.state = "ready"
            job.lease_expires_at = None
            job.error_code = None
            job.error_message = None
            job.diagnostics = None
            db.commit()
            logger.info("Kích hoạt thành công phiên bản %s cho nguồn %s", version.id, source.id)

        except UnsupportedFormatError as exc:
            job.state = "failed"
            job.error_code = "UNSUPPORTED_FORMAT"
            job.error_message = str(exc)
            job.diagnostics = {"errors": [{"reason": str(exc)}]}
            job.lease_expires_at = None
            db.commit()
            return
        except MalformedSourceError as exc:
            job.state = "failed"
            job.error_code = "MALFORMED_SOURCE"
            job.error_message = str(exc)
            job.diagnostics = {"errors": [{"reason": str(exc)}]}
            job.lease_expires_at = None
            db.commit()
            return
        except Exception as exc:
            logger.exception("Lỗi không mong muốn trong khi xử lý job %s: %s", job_id_str, exc)
            retries = getattr(self.request, "retries", 0) if hasattr(self, "request") else 0
            max_r = getattr(self, "max_retries", 3)
            if retries >= max_r:
                job.state = "failed"
                job.error_code = "MAX_RETRIES_EXCEEDED"
                job.error_message = f"Vượt quá số lần thử lại tối đa: {exc}"
                job.lease_expires_at = None
                db.commit()
                return
            else:
                db.commit()
                raise self.retry(exc=exc, countdown=2 ** retries)

"""Source lifecycle persistence services, atomic activation, and job reconciliation."""
from datetime import datetime, timezone, timedelta
import hashlib
import logging
import os
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

from fastapi import HTTPException
from sqlalchemy import func, select, delete
from sqlalchemy.orm import Session

from app.auth.policy import (
    allowed_dataset_ids,
    current_account,
    require_admin,
)
from app.database.datasets import recheck_response
from app.database.models import (
    Account,
    CanonicalRecord,
    Dataset,
    ImportJob,
    ParseRun,
    Source,
    SourceVersion,
    utcnow,
)
from app.rag.parsers.profiles import get_profile
from app.workers.tasks import get_source_storage_path, process_ingestion_job

logger = logging.getLogger("rag.audit")


def save_uploaded_source(
    db: Session,
    actor: Account,
    dataset_id: UUID,
    logical_filename: str,
    profile_id: str,
    content_bytes: bytes,
    mime_type: str,
) -> tuple[Source, SourceVersion, ImportJob, bool]:
    """Lưu trữ tệp nguồn tải lên, quản lý phiên bản bất biến và xếp hàng xử lý."""
    require_admin(current_account(db, actor))

    dataset = db.get(Dataset, dataset_id)
    if dataset is None:
        raise HTTPException(404, "Không tìm thấy Dataset")

    try:
        get_profile(profile_id)
    except ValueError as exc:
        raise HTTPException(400, f"Hồ sơ nguồn không hợp lệ: {profile_id}") from exc

    content_hash = hashlib.sha256(content_bytes).hexdigest()

    # Tìm nguồn hiện có chưa bị xóa theo (dataset_id, logical_filename)
    source = db.scalar(
        select(Source).where(
            Source.dataset_id == dataset_id,
            Source.logical_filename == logical_filename,
            Source.deleted_at.is_(None),
        )
    )

    if source is not None:
        # Xử lý trùng lặp nội dung (Idempotent Deduplication - D-01)
        existing_ver = db.scalar(
            select(SourceVersion).where(
                SourceVersion.source_id == source.id,
                SourceVersion.content_hash == content_hash,
            )
        )
        if existing_ver is not None:
            latest_job = db.scalar(
                select(ImportJob)
                .where(ImportJob.source_version_id == existing_ver.id)
                .order_by(ImportJob.created_at.desc())
            )
            logger.info(
                "Nội dung trùng hash %s trong dataset %s, bỏ qua tạo version mới (no-op)",
                content_hash,
                dataset_id,
            )
            return source, existing_ver, latest_job, False

        # Nội dung khác SHA-256: tạo version tiếp theo
        max_ver = db.scalar(
            select(func.coalesce(func.max(SourceVersion.version_number), 0)).where(
                SourceVersion.source_id == source.id
            )
        )
        version_number = (max_ver or 0) + 1

        storage_key = str(uuid4())
        path = get_source_storage_path(storage_key)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content_bytes)

        new_version = SourceVersion(
            source_id=source.id,
            version_number=version_number,
            content_hash=content_hash,
            storage_key=storage_key,
            size_bytes=len(content_bytes),
            mime_type=mime_type,
        )
        db.add(new_version)
        db.flush()

        job = ImportJob(
            source_version_id=new_version.id,
            state="queued",
            attempt_count=0,
            max_attempts=3,
        )
        db.add(job)
        db.commit()

        try:
            process_ingestion_job.delay(str(job.id))
        except Exception as exc:
            logger.warning("Không thể enqueue Celery job %s: %s", job.id, exc)

        logger.warning(
            "actor=%s action=%s dataset=%s source=%s version=%s",
            actor.id,
            "source.new_version",
            dataset_id,
            source.id,
            version_number,
        )
        return source, new_version, job, True

    # Nguồn mới hoàn toàn
    source = Source(
        dataset_id=dataset_id,
        logical_filename=logical_filename,
        profile_id=profile_id,
    )
    db.add(source)
    db.flush()

    storage_key = str(uuid4())
    path = get_source_storage_path(storage_key)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content_bytes)

    new_version = SourceVersion(
        source_id=source.id,
        version_number=1,
        content_hash=content_hash,
        storage_key=storage_key,
        size_bytes=len(content_bytes),
        mime_type=mime_type,
    )
    db.add(new_version)
    db.flush()

    job = ImportJob(
        source_version_id=new_version.id,
        state="queued",
        attempt_count=0,
        max_attempts=3,
    )
    db.add(job)
    db.commit()

    try:
        process_ingestion_job.delay(str(job.id))
    except Exception as exc:
        logger.warning("Không thể enqueue Celery job %s: %s", job.id, exc)

    logger.warning(
        "actor=%s action=%s dataset=%s source=%s version=1",
        actor.id,
        "source.create",
        dataset_id,
        source.id,
    )
    return source, new_version, job, True


def retry_failed_job(
    db: Session,
    actor: Account,
    dataset_id: UUID,
    source_id: UUID,
) -> ImportJob:
    """Thử lại tác vụ xử lý gần nhất đang ở trạng thái thất bại."""
    require_admin(current_account(db, actor))

    source = db.get(Source, source_id)
    if source is None or source.dataset_id != dataset_id or source.deleted_at is not None:
        raise HTTPException(404, "Không tìm thấy Nguồn dữ liệu")

    job = db.scalar(
        select(ImportJob)
        .join(SourceVersion, ImportJob.source_version_id == SourceVersion.id)
        .where(SourceVersion.source_id == source.id)
        .order_by(ImportJob.created_at.desc())
    )
    if job is None:
        raise HTTPException(404, "Không tìm thấy tác vụ xử lý của nguồn")

    if job.state != "failed":
        raise HTTPException(400, "Chỉ có thể thử lại tác vụ ở trạng thái thất bại (failed)")

    job.state = "queued"
    job.error_code = None
    job.error_message = None
    job.diagnostics = None
    job.lease_expires_at = None
    db.commit()

    try:
        process_ingestion_job.delay(str(job.id))
    except Exception as exc:
        logger.warning("Không thể enqueue Celery retry job %s: %s", job.id, exc)

    logger.warning(
        "actor=%s action=%s dataset=%s source=%s job=%s",
        actor.id,
        "source.retry",
        dataset_id,
        source.id,
        job.id,
    )
    return job


def reprocess_active_source(
    db: Session,
    actor: Account,
    dataset_id: UUID,
    source_id: UUID,
) -> ImportJob:
    """Chạy lại tác vụ xử lý trên phiên bản đang hoạt động (không tạo phiên bản mới)."""
    require_admin(current_account(db, actor))

    source = db.get(Source, source_id)
    if source is None or source.dataset_id != dataset_id or source.deleted_at is not None:
        raise HTTPException(404, "Không tìm thấy Nguồn dữ liệu")

    if source.active_version_id is None:
        raise HTTPException(400, "Nguồn chưa có phiên bản đang hoạt động để xử lý lại")

    # BẮT BUỘC (D-01, D-10): Chạy lại trên chính phiên bản active hiện tại, KHÔNG tạo phiên bản mới.
    job = ImportJob(
        source_version_id=source.active_version_id,
        state="queued",
        attempt_count=0,
        max_attempts=3,
    )
    db.add(job)
    db.commit()

    try:
        process_ingestion_job.delay(str(job.id))
    except Exception as exc:
        logger.warning("Không thể enqueue Celery reprocess job %s: %s", job.id, exc)

    logger.warning(
        "actor=%s action=%s dataset=%s source=%s version=%s",
        actor.id,
        "source.reprocess",
        dataset_id,
        source.id,
        source.active_version_id,
    )
    return job


def tombstone_source(
    db: Session,
    actor: Account,
    dataset_id: UUID,
    source_id: UUID,
) -> None:
    """Đánh dấu tombstone nguồn ngay lập tức và ngăn chặn các job đang chạy xuất bản."""
    require_admin(current_account(db, actor))

    source = db.get(Source, source_id)
    if source is None or source.dataset_id != dataset_id or source.deleted_at is not None:
        raise HTTPException(404, "Không tìm thấy Nguồn dữ liệu")

    source.deleted_at = utcnow()
    db.commit()

    logger.warning(
        "actor=%s action=%s dataset=%s source=%s",
        actor.id,
        "source.tombstone",
        dataset_id,
        source.id,
    )


def reconcile_stale_jobs(db: Session) -> int:
    """Phục hồi các job bị treo do worker gặp sự cố (quá hạn lease)."""
    now = utcnow()
    stale_jobs = db.scalars(
        select(ImportJob).where(
            ImportJob.state == "processing",
            ImportJob.lease_expires_at < now,
        )
    ).all()

    for job in stale_jobs:
        version = db.get(SourceVersion, job.source_version_id)
        source = db.get(Source, version.source_id) if version else None

        if source and source.deleted_at is not None:
            job.state = "failed"
            job.error_code = "SOURCE_DELETED"
            job.error_message = "Nguồn đã bị xóa"
            job.lease_expires_at = None
        elif job.attempt_count < job.max_attempts:
            job.state = "queued"
            job.lease_expires_at = None
            try:
                process_ingestion_job.delay(str(job.id))
            except Exception as exc:
                logger.warning("Không thể đưa job %s vào hàng đợi lại: %s", job.id, exc)
        else:
            job.state = "failed"
            job.error_code = "LEASE_EXPIRED_MAX_ATTEMPTS"
            job.error_message = "Hết hạn lease và đã vượt quá số lần thử lại tối đa"
            job.lease_expires_at = None

    db.commit()
    return len(stale_jobs)

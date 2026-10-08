from uuid import uuid4
import pytest
from app.database.models import (
    Account,
    CanonicalRecord,
    Dataset,
    ImportJob,
    ParseRun,
    Source,
    SourceVersion,
)
from app.database.retrieval import execute_hybrid_retrieval, search_lexical_records
from app.database.sources import index_source_version
from app.providers.fake import FakeEmbeddingAdapter
from app.rag.filters import ScopeCriteria


def test_exact_identifier_disambiguation_dh001_vs_dh010(db):
    """Xác minh RAG-02: Truy vấn DH001 trả về chính xác bản ghi DH001,

    tuyệt đối KHÔNG nhầm lẫn hoặc ưu tiên nhầm DH010.
    """
    admin = Account(username="admin_retrieval", display_name="Admin Retrieval", password_hash="hash", role="admin")
    db.add(admin)
    dataset = Dataset(name=f"Dataset-Logistics-{uuid4().hex[:8]}")
    db.add(dataset)
    db.flush()

    source = Source(dataset_id=dataset.id, logical_filename="sorting_events.log", profile_id="text_log")
    db.add(source)
    db.flush()

    version = SourceVersion(
        source_id=source.id, version_number=1, content_hash="hash_retrieval_1", storage_key="key1", size_bytes=200, mime_type="text/plain"
    )
    db.add(version)
    db.flush()
    source.active_version_id = version.id
    db.flush()

    job = ImportJob(source_version_id=version.id, state="ready")
    db.add(job)
    db.flush()

    parse_run = ParseRun(
        source_version_id=version.id, job_id=job.id, parser_name="text_log", parser_version="1.0", status="published"
    )
    db.add(parse_run)
    db.flush()

    # Tạo 2 bản ghi log dễ gây nhầm lẫn: DH001 và DH010
    rec_dh001 = CanonicalRecord(
        parse_run_id=parse_run.id,
        source_version_id=version.id,
        dataset_id=dataset.id,
        position=1,
        locator_data={"line_start": 1, "line_end": 2},
        content_text="[ERROR] Đơn hàng DH001 bị kẹt tại máng chuyền số 4 do kích thước vượt chuẩn.",
        record_metadata={"order_id": "DH001"}
    )
    rec_dh010 = CanonicalRecord(
        parse_run_id=parse_run.id,
        source_version_id=version.id,
        dataset_id=dataset.id,
        position=2,
        locator_data={"line_start": 3, "line_end": 4},
        content_text="[INFO] Đơn hàng DH010 đã phân loại thành công vào bao 9.",
        record_metadata={"order_id": "DH010"}
    )
    db.add_all([rec_dh001, rec_dh010])
    db.commit()

    # Index vector bằng FakeEmbeddingAdapter
    fake_provider = FakeEmbeddingAdapter()
    index_source_version(db, version.id, provider=fake_provider)

    # 1. Kiểm tra nhánh lexical matcher riêng biệt
    lexical_results = search_lexical_records(
        db=db,
        identifiers=["DH001"],
        dataset_ids={dataset.id},
    )
    assert len(lexical_results) == 1
    assert "DH001" in lexical_results[0].text
    assert "DH010" not in lexical_results[0].text

    # 2. Kiểm tra toàn bộ luồng Hybrid Retrieval với query tìm kiếm DH001
    query = "Sự cố kẹt đơn hàng DH001"
    query_vec = list(fake_provider.embed((query,))[0])
    criteria = ScopeCriteria(allowed_dataset_ids={dataset.id})

    results = execute_hybrid_retrieval(
        db=db,
        query=query,
        query_vector=query_vec,
        scope_criteria=criteria,
        top_k=5,
    )

    assert len(results) >= 1
    # Bản ghi đầu tiên phải là DH001 do được lexical match ưu tiên
    assert "DH001" in results[0].text
    assert "DH010" not in results[0].text


def test_hybrid_retrieval_profile_filtering(db):
    """Xác minh RAG-03: Lọc theo profile_id cách ly kết quả giữa Log và SOP."""
    admin = Account(username="admin_prof", display_name="Admin Profile", password_hash="hash", role="admin")
    db.add(admin)
    dataset = Dataset(name=f"Dataset-Prof-{uuid4().hex[:8]}")
    db.add(dataset)
    db.flush()

    # Nguồn 1: Log
    src_log = Source(dataset_id=dataset.id, logical_filename="app.log", profile_id="text_log")
    db.add(src_log)
    db.flush()
    ver_log = SourceVersion(source_id=src_log.id, version_number=1, content_hash="h1", storage_key="k1", size_bytes=100, mime_type="text/plain")
    db.add(ver_log)
    db.flush()
    src_log.active_version_id = ver_log.id
    job_log = ImportJob(source_version_id=ver_log.id, state="ready")
    db.add(job_log)
    db.flush()
    run_log = ParseRun(source_version_id=ver_log.id, job_id=job_log.id, parser_name="text_log", parser_version="1.0", status="published")
    db.add(run_log)
    db.flush()
    rec_log = CanonicalRecord(
        parse_run_id=run_log.id, source_version_id=ver_log.id, dataset_id=dataset.id, position=1,
        locator_data={"line_start": 1}, content_text="Lỗi kết nối cơ sở dữ liệu ERR-502 tại dịch vụ vận chuyển",
    )
    db.add(rec_log)

    # Nguồn 2: SOP tài liệu
    src_sop = Source(dataset_id=dataset.id, logical_filename="sop_huong_dan.txt", profile_id="sop")
    db.add(src_sop)
    db.flush()
    ver_sop = SourceVersion(source_id=src_sop.id, version_number=1, content_hash="h2", storage_key="k2", size_bytes=100, mime_type="text/plain")
    db.add(ver_sop)
    db.flush()
    src_sop.active_version_id = ver_sop.id
    job_sop = ImportJob(source_version_id=ver_sop.id, state="ready")
    db.add(job_sop)
    db.flush()
    run_sop = ParseRun(source_version_id=ver_sop.id, job_id=job_sop.id, parser_name="text_log", parser_version="1.0", status="published")
    db.add(run_sop)
    db.flush()
    rec_sop = CanonicalRecord(
        parse_run_id=run_sop.id, source_version_id=ver_sop.id, dataset_id=dataset.id, position=1,
        locator_data={"line_start": 1}, content_text="Quy trình hướng dẫn khởi động lại service khi gặp ERR-502",
    )
    db.add(rec_sop)
    db.commit()

    fake_provider = FakeEmbeddingAdapter()
    index_source_version(db, ver_log.id, provider=fake_provider)
    index_source_version(db, ver_sop.id, provider=fake_provider)

    # Truy vấn chỉ với profile "sop"
    query = "ERR-502 xử lý thế nào"
    query_vec = list(fake_provider.embed((query,))[0])
    criteria = ScopeCriteria(allowed_dataset_ids={dataset.id}, profile_id="sop")

    results = execute_hybrid_retrieval(
        db=db,
        query=query,
        query_vector=query_vec,
        scope_criteria=criteria,
        top_k=5,
    )

    assert len(results) == 1
    assert "Quy trình hướng dẫn" in results[0].text
    assert "Lỗi kết nối cơ sở dữ liệu" not in results[0].text

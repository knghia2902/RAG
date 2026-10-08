from uuid import uuid4
import pytest
from app.database.models import (
    Account,
    CanonicalRecord,
    Dataset,
    DatasetGrant,
    ImportJob,
    ParseRun,
    Source,
    SourceVersion,
)
from app.database.retrieval import execute_hybrid_retrieval
from app.database.sources import index_source_version
from app.providers.fake import FakeEmbeddingAdapter
from app.rag.filters import ScopeCriteria, ScopeFilterBuilder


def test_retrieval_acl_dataset_isolation_and_rejection(db):
    """Xác minh AUTH-04: Kỹ thuật viên không bao giờ truy xuất được tài liệu

    từ Dataset không có quyền, kể cả cố tình chỉ định dataset_id.
    """
    # 1. Tạo Tech 1 và Admin
    tech = Account(username="tech_acl", display_name="Tech ACL", password_hash="hash", role="technician")
    admin = Account(username="admin_acl", display_name="Admin ACL", password_hash="hash", role="admin")
    db.add_all([tech, admin])

    # 2. Tạo Dataset A (cho Tech) và Dataset B (bảo mật, chỉ Admin)
    ds_allowed = Dataset(name=f"Dataset-Public-{uuid4().hex[:8]}")
    ds_secret = Dataset(name=f"Dataset-Confidential-{uuid4().hex[:8]}")
    db.add_all([ds_allowed, ds_secret])
    db.flush()

    # Cấp quyền Dataset A cho Tech
    grant = DatasetGrant(account_id=tech.id, dataset_id=ds_allowed.id)
    db.add(grant)
    db.flush()

    # 3. Tạo tài liệu công khai trong Dataset A
    src_pub = Source(dataset_id=ds_allowed.id, logical_filename="public_sop.txt", profile_id="sop")
    db.add(src_pub)
    db.flush()
    ver_pub = SourceVersion(source_id=src_pub.id, version_number=1, content_hash="hpub", storage_key="kpub", size_bytes=100, mime_type="text/plain")
    db.add(ver_pub)
    db.flush()
    src_pub.active_version_id = ver_pub.id
    job_pub = ImportJob(source_version_id=ver_pub.id, state="ready")
    db.add(job_pub)
    db.flush()
    run_pub = ParseRun(source_version_id=ver_pub.id, job_id=job_pub.id, parser_name="text_log", parser_version="1.0", status="published")
    db.add(run_pub)
    db.flush()
    rec_pub = CanonicalRecord(
        parse_run_id=run_pub.id, source_version_id=ver_pub.id, dataset_id=ds_allowed.id, position=1,
        locator_data={"line_start": 1}, content_text="Hướng dẫn xử lý đơn hàng thường quy tại kho tổng",
    )
    db.add(rec_pub)

    # 4. Tạo tài liệu mật trong Dataset B
    src_sec = Source(dataset_id=ds_secret.id, logical_filename="secret_doc.txt", profile_id="sop")
    db.add(src_sec)
    db.flush()
    ver_sec = SourceVersion(source_id=src_sec.id, version_number=1, content_hash="hsec", storage_key="ksec", size_bytes=100, mime_type="text/plain")
    db.add(ver_sec)
    db.flush()
    src_sec.active_version_id = ver_sec.id
    job_sec = ImportJob(source_version_id=ver_sec.id, state="ready")
    db.add(job_sec)
    db.flush()
    run_sec = ParseRun(source_version_id=ver_sec.id, job_id=job_sec.id, parser_name="text_log", parser_version="1.0", status="published")
    db.add(run_sec)
    db.flush()
    rec_sec = CanonicalRecord(
        parse_run_id=run_sec.id, source_version_id=ver_sec.id, dataset_id=ds_secret.id, position=1,
        locator_data={"line_start": 1}, content_text="BÍ MẬT LOGISTICS QUỐC GIA - Kế hoạch luân chuyển kho đặc biệt",
    )
    db.add(rec_sec)
    db.commit()

    # Index embeddings
    fake_provider = FakeEmbeddingAdapter()
    index_source_version(db, ver_pub.id, provider=fake_provider)
    index_source_version(db, ver_sec.id, provider=fake_provider)

    # 5. Tech thực hiện truy vấn hợp lệ trong quyền được cấp
    query = "Kế hoạch luân chuyển kho"
    query_vec = list(fake_provider.embed((query,))[0])

    criteria_tech = ScopeFilterBuilder.build_filters(
        allowed_dataset_ids={ds_allowed.id},
    )
    results = execute_hybrid_retrieval(
        db=db,
        query=query,
        query_vector=query_vec,
        scope_criteria=criteria_tech,
        top_k=10,
    )

    # Xác minh: KHÔNG CÓ bất kỳ chunk nào chứa tài liệu mật của Dataset B
    assert len(results) > 0
    for r in results:
        assert r.dataset_id != ds_secret.id
        assert "BÍ MẬT LOGISTICS QUỐC GIA" not in r.text

    # 6. Kẻ xấu cố tình đưa Dataset B vào target_dataset_ids
    with pytest.raises(PermissionError) as exc_info:
        ScopeFilterBuilder.build_filters(
            allowed_dataset_ids={ds_allowed.id},
            target_dataset_ids={ds_secret.id},
        )
    assert "Không có quyền truy cập" in str(exc_info.value)

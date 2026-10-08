from uuid import uuid4
import pytest
from sqlalchemy import select
from app.database.models import (
    Account,
    CanonicalRecord,
    Dataset,
    EmbeddingRecord,
    ImportJob,
    ParseRun,
    Source,
    SourceVersion,
)
from app.database.sources import index_source_version, delete_source_embeddings, tombstone_source
from app.providers.fake import FakeEmbeddingAdapter


def test_index_and_tombstone_source_embeddings(db):
    # Setup account and dataset
    admin = Account(username="admin_vec", display_name="Admin Vector", password_hash="hash", role="admin")
    db.add(admin)
    dataset = Dataset(name=f"Dataset-{uuid4().hex[:8]}")
    db.add(dataset)
    db.flush()

    source = Source(dataset_id=dataset.id, logical_filename="sop_logistics.txt", profile_id="text_log")
    db.add(source)
    db.flush()

    version = SourceVersion(
        source_id=source.id, version_number=1, content_hash="hash1", storage_key="key1", size_bytes=150, mime_type="text/plain"
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

    # Add canonical records, one containing a secret token
    rec1 = CanonicalRecord(
        parse_run_id=parse_run.id,
        source_version_id=version.id,
        dataset_id=dataset.id,
        position=1,
        locator_data={"line_start": 1, "line_end": 5},
        content_text="Quy trình xuất kho: kiểm tra mã đơn DH001 tại cổng 3",
        record_metadata={"order_id": "DH001"}
    )
    rec2 = CanonicalRecord(
        parse_run_id=parse_run.id,
        source_version_id=version.id,
        dataset_id=dataset.id,
        position=2,
        locator_data={"line_start": 6, "line_end": 10},
        content_text="Kết nối hệ thống WMS với token Bearer 1234567890abcdef1234567890 thành công",
        record_metadata={"system": "WMS"}
    )
    db.add_all([rec1, rec2])
    db.commit()

    # Run vector indexing with FakeEmbeddingAdapter
    fake_provider = FakeEmbeddingAdapter()
    indexed_count = index_source_version(db, version.id, provider=fake_provider)
    assert indexed_count == 2

    # Verify embeddings were inserted in database
    embeddings = db.scalars(
        select(EmbeddingRecord).where(EmbeddingRecord.source_version_id == version.id)
    ).all()
    assert len(embeddings) == 2
    for emb in embeddings:
        assert emb.model_name == fake_provider.index.model
        assert emb.dimension == 1536
        assert len(emb.embedding) == 1536

    # Test re-indexing idempotency (should replace without duplicating)
    reindexed_count = index_source_version(db, version.id, provider=fake_provider)
    assert reindexed_count == 2
    embeddings_after = db.scalars(
        select(EmbeddingRecord).where(EmbeddingRecord.source_version_id == version.id)
    ).all()
    assert len(embeddings_after) == 2

    # Test tombstone source removes embeddings (DATA-05)
    tombstone_source(db, admin, dataset.id, source.id)
    embeddings_tombstoned = db.scalars(
        select(EmbeddingRecord).where(EmbeddingRecord.source_version_id == version.id)
    ).all()
    assert len(embeddings_tombstoned) == 0

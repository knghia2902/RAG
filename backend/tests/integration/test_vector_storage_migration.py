import subprocess
from uuid import uuid4
import pytest
from sqlalchemy import text
from app.database.session import engine
from app.database.models import Account, Dataset, Source, SourceVersion, CanonicalRecord, EmbeddingRecord, ChatSession, ChatMessage


def test_migration_0003_pgvector_and_chat(db):
    subprocess.run(["python", "-m", "alembic", "upgrade", "head"], check=True)
    with engine.connect() as connection:
        assert connection.scalar(text("SELECT version_num FROM alembic_version")) in ("0003_pgvector_and_chat", "0004_incident_analysis", "0005_incident_reports", "0006_extracted_images")
        tables = connection.scalars(text(
            "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"
        )).all()
        for t in ("embedding_records", "chat_sessions", "chat_messages"):
            assert t in tables, f"Table {t} missing"

        # Check vector extension
        ext = connection.scalar(text("SELECT extname FROM pg_extension WHERE extname='vector'"))
        assert ext == "vector"

        # Check constraints on chat_messages
        constraints = connection.scalars(text(
            "SELECT conname FROM pg_constraint WHERE conrelid = 'chat_messages'::regclass"
        )).all()
        assert "chat_message_role_valid" in constraints


def test_embedding_record_vector_cosine_distance(db):
    # Ensure schema is up to date
    subprocess.run(["python", "-m", "alembic", "upgrade", "head"], check=True)

    # Create dummy account, dataset, source, version, canonical record
    account = Account(username="tech_vec", display_name="Tech Vector", password_hash="hash", role="technician")
    db.add(account)
    dataset = Dataset(name=f"Dataset-{uuid4().hex[:8]}")
    db.add(dataset)
    db.flush()

    source = Source(dataset_id=dataset.id, logical_filename="test.log", profile_id="text_log")
    db.add(source)
    db.flush()

    version = SourceVersion(
        source_id=source.id, version_number=1, content_hash="hash1", storage_key="key1", size_bytes=100, mime_type="text/plain"
    )
    db.add(version)
    db.flush()
    source.active_version_id = version.id
    db.flush()

    from app.database.models import ImportJob, ParseRun
    job = ImportJob(source_version_id=version.id, state="ready")
    db.add(job)
    db.flush()
    parse_run = ParseRun(source_version_id=version.id, job_id=job.id, parser_name="text_log", parser_version="1.0", status="published")
    db.add(parse_run)
    db.flush()

    record1 = CanonicalRecord(
        parse_run_id=parse_run.id,
        source_version_id=version.id,
        dataset_id=dataset.id,
        position=1,
        locator_data={"line_start": 1, "line_end": 5},
        content_text="Đơn hàng DH001 bị lỗi kết nối WMS",
        record_metadata={"order_id": "DH001"}
    )
    record2 = CanonicalRecord(
        parse_run_id=parse_run.id,
        source_version_id=version.id,
        dataset_id=dataset.id,
        position=2,
        locator_data={"line_start": 6, "line_end": 10},
        content_text="Đơn hàng DH010 đã xuất kho thành công",
        record_metadata={"order_id": "DH010"}
    )
    db.add_all([record1, record2])
    db.flush()

    # Create 1536-dim dummy vectors
    vec1 = [0.1] * 1536
    vec2 = [-0.1] * 1536
    idx_ver = uuid4()

    emb1 = EmbeddingRecord(
        canonical_record_id=record1.id,
        dataset_id=dataset.id,
        source_version_id=version.id,
        model_name="text-embedding-3-small",
        dimension=1536,
        index_version=idx_ver,
        embedding=vec1
    )
    emb2 = EmbeddingRecord(
        canonical_record_id=record2.id,
        dataset_id=dataset.id,
        source_version_id=version.id,
        model_name="text-embedding-3-small",
        dimension=1536,
        index_version=idx_ver,
        embedding=vec2
    )
    db.add_all([emb1, emb2])
    db.commit()

    # Test query using cosine distance (<=>)
    query_vec = [0.1] * 1536
    results = db.query(EmbeddingRecord).order_by(EmbeddingRecord.embedding.cosine_distance(query_vec)).all()
    assert len(results) >= 2
    assert results[0].id == emb1.id

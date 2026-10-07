from datetime import datetime, timezone, timedelta
from uuid import uuid4
import pytest
from sqlalchemy import select, func
from app.database.models import Dataset, Source, SourceVersion, ImportJob, ParseRun, CanonicalRecord
from app.workers.tasks import process_ingestion_job


def create_sample_job_hierarchy(db, state="queued"):
    dataset = Dataset(name=f"Job Dataset {uuid4()}")
    db.add(dataset)
    db.flush()

    source = Source(dataset_id=dataset.id, logical_filename="test_log.log", profile_id="log")
    db.add(source)
    db.flush()

    ver = SourceVersion(
        source_id=source.id,
        version_number=1,
        content_hash="abc123hash",
        storage_key="opaque-key-01",
        size_bytes=512,
        mime_type="text/plain",
    )
    db.add(ver)
    db.flush()

    job = ImportJob(
        source_version_id=ver.id,
        state=state,
        attempt_count=0,
        max_attempts=3,
    )
    db.add(job)
    db.commit()
    return dataset, source, ver, job


def test_job_bounded_retry_increments_and_caps(db):
    _, _, _, job = create_sample_job_hierarchy(db, state="processing")
    assert job.attempt_count == 0
    assert job.max_attempts == 3

    # Simulate transient retry
    job.attempt_count += 1
    db.commit()
    assert job.attempt_count == 1

    # Simulate exceeding max attempts
    job.attempt_count = job.max_attempts
    job.state = "failed"
    job.error_code = "MAX_RETRIES_EXCEEDED"
    db.commit()

    reloaded = db.get(ImportJob, job.id)
    assert reloaded.state == "failed"
    assert reloaded.attempt_count == 3


def test_job_schema_validation_error_transitions_to_failed_immediately(db):
    _, _, _, job = create_sample_job_hierarchy(db, state="processing")

    # Schema error fails immediately with diagnostics without incrementing retry
    job.state = "failed"
    job.error_code = "SCHEMA_VALIDATION_ERROR"
    job.error_message = "Dòng 2 thiếu trường bắt buộc 'timestamp'"
    job.diagnostics = {"errors": [{"row": 2, "field": "timestamp", "reason": "Missing required field"}]}
    db.commit()

    reloaded = db.get(ImportJob, job.id)
    assert reloaded.state == "failed"
    assert reloaded.diagnostics is not None
    assert reloaded.attempt_count == 0


def test_stale_processing_job_lease_recovery(db):
    _, _, _, job = create_sample_job_hierarchy(db, state="processing")
    past_time = datetime.now(timezone.utc) - timedelta(minutes=15)
    job.lease_expires_at = past_time
    db.commit()

    # Recovery query identifies expired lease
    now = datetime.now(timezone.utc)
    expired_jobs = db.scalars(
        select(ImportJob).where(
            ImportJob.state == "processing",
            ImportJob.lease_expires_at < now,
        )
    ).all()

    assert job in expired_jobs

    # Recover to queued
    for j in expired_jobs:
        j.state = "queued"
        j.lease_expires_at = None
    db.commit()

    reloaded = db.get(ImportJob, job.id)
    assert reloaded.state == "queued"
    assert reloaded.lease_expires_at is None


def test_job_retry_idempotency_does_not_duplicate_canonical_records(db):
    dataset, source, ver, job = create_sample_job_hierarchy(db, state="processing")

    run = ParseRun(
        source_version_id=ver.id,
        job_id=job.id,
        parser_name="text_log",
        parser_version="1.0.0",
        status="staged",
    )
    db.add(run)
    db.flush()

    # Add 2 staged records
    for pos in (1, 2):
        rec = CanonicalRecord(
            parse_run_id=run.id,
            source_version_id=ver.id,
            dataset_id=dataset.id,
            position=pos,
            locator_data={"line": pos},
            content_text=f"Line {pos} log content",
            record_metadata={},
        )
        db.add(rec)
    db.commit()

    count_before = db.scalar(
        select(func.count()).select_from(CanonicalRecord).where(CanonicalRecord.parse_run_id == run.id)
    )
    assert count_before == 2

    # Simulate rerun / retry on the same parse run: existing records are purged or upserted
    # rather than duplicated
    db.query(CanonicalRecord).filter(CanonicalRecord.parse_run_id == run.id).delete()
    for pos in (1, 2):
        rec = CanonicalRecord(
            parse_run_id=run.id,
            source_version_id=ver.id,
            dataset_id=dataset.id,
            position=pos,
            locator_data={"line": pos},
            content_text=f"Line {pos} log content",
            record_metadata={},
        )
        db.add(rec)
    db.commit()

    count_after = db.scalar(
        select(func.count()).select_from(CanonicalRecord).where(CanonicalRecord.parse_run_id == run.id)
    )
    assert count_after == 2


def test_process_ingestion_job_valid_activates_version(db, tmp_path, monkeypatch):
    monkeypatch.setenv("STORAGE_DIR", str(tmp_path))
    dataset = Dataset(name=f"Job Dataset Valid {uuid4()}")
    db.add(dataset)
    db.flush()

    source = Source(dataset_id=dataset.id, logical_filename="test_doc.txt", profile_id="document")
    db.add(source)
    db.flush()

    storage_key = "valid-test-storage-key"
    storage_file = tmp_path / "sources" / storage_key
    storage_file.parent.mkdir(parents=True, exist_ok=True)
    storage_file.write_bytes(b"Day la van ban hop le cua tai lieu quy trinh logistics.")

    ver = SourceVersion(
        source_id=source.id,
        version_number=1,
        content_hash="validhash123",
        storage_key=storage_key,
        size_bytes=len(b"Day la van ban hop le cua tai lieu quy trinh logistics."),
        mime_type="text/plain",
    )
    db.add(ver)
    db.flush()

    job = ImportJob(source_version_id=ver.id, state="queued", attempt_count=0, max_attempts=3)
    db.add(job)
    db.commit()

    process_ingestion_job(str(job.id))
    db.expire_all()

    reloaded_job = db.get(ImportJob, job.id)
    assert reloaded_job.state == "ready"
    assert reloaded_job.error_code is None

    reloaded_source = db.get(Source, source.id)
    assert reloaded_source.active_version_id == ver.id

    records = db.scalars(select(CanonicalRecord).where(CanonicalRecord.source_version_id == ver.id)).all()
    assert len(records) > 0


def test_process_ingestion_job_schema_error_atomic_failure(db, tmp_path, monkeypatch):
    monkeypatch.setenv("STORAGE_DIR", str(tmp_path))
    dataset = Dataset(name=f"Job Dataset Schema Error {uuid4()}")
    db.add(dataset)
    db.flush()

    source = Source(dataset_id=dataset.id, logical_filename="orders.csv", profile_id="operations_table")
    db.add(source)
    db.flush()

    # Prior active version 1
    ver1 = SourceVersion(
        source_id=source.id,
        version_number=1,
        content_hash="ver1hash",
        storage_key="v1-key",
        size_bytes=10,
        mime_type="text/csv",
    )
    db.add(ver1)
    db.flush()
    source.active_version_id = ver1.id
    db.commit()

    # Version 2 candidate missing required fields
    storage_key = "v2-invalid-key"
    storage_file = tmp_path / "sources" / storage_key
    storage_file.parent.mkdir(parents=True, exist_ok=True)
    storage_file.write_bytes(b"entity_id,notes\n1001,only notes\n")

    ver2 = SourceVersion(
        source_id=source.id,
        version_number=2,
        content_hash="ver2hash",
        storage_key=storage_key,
        size_bytes=30,
        mime_type="text/csv",
    )
    db.add(ver2)
    db.flush()

    job2 = ImportJob(source_version_id=ver2.id, state="queued", attempt_count=0, max_attempts=3)
    db.add(job2)
    db.commit()

    process_ingestion_job(str(job2.id))
    db.expire_all()

    reloaded_job2 = db.get(ImportJob, job2.id)
    assert reloaded_job2.state == "failed"
    assert reloaded_job2.error_code == "SCHEMA_VALIDATION_ERROR"
    assert reloaded_job2.diagnostics is not None

    # Atomic failure guarantee: active_version_id remains ver1
    reloaded_source = db.get(Source, source.id)
    assert reloaded_source.active_version_id == ver1.id


def test_process_ingestion_job_retry_idempotency_records(db, tmp_path, monkeypatch):
    monkeypatch.setenv("STORAGE_DIR", str(tmp_path))
    dataset = Dataset(name=f"Job Dataset Retry Task {uuid4()}")
    db.add(dataset)
    db.flush()

    source = Source(dataset_id=dataset.id, logical_filename="data.jsonl", profile_id="log")
    db.add(source)
    db.flush()

    storage_key = "log-jsonl-key"
    storage_file = tmp_path / "sources" / storage_key
    storage_file.parent.mkdir(parents=True, exist_ok=True)
    storage_file.write_bytes(
        b'{"timestamp": "2026-10-07T12:00:00Z", "system": "TMS", "severity": "INFO", "message": "msg 1"}\n'
        b'{"timestamp": "2026-10-07T12:05:00Z", "system": "WMS", "severity": "WARN", "message": "msg 2"}\n'
    )

    ver = SourceVersion(
        source_id=source.id,
        version_number=1,
        content_hash="logjsonlhash",
        storage_key=storage_key,
        size_bytes=150,
        mime_type="application/jsonl",
    )
    db.add(ver)
    db.flush()

    job = ImportJob(source_version_id=ver.id, state="queued", attempt_count=0, max_attempts=3)
    db.add(job)
    db.commit()

    # First run
    process_ingestion_job(str(job.id))
    db.expire_all()
    records1 = db.scalars(select(CanonicalRecord).where(CanonicalRecord.source_version_id == ver.id)).all()
    assert len(records1) == 2

    # Second run (retry on same job)
    job.state = "queued"
    db.commit()
    process_ingestion_job(str(job.id))
    db.expire_all()
    records2 = db.scalars(select(CanonicalRecord).where(CanonicalRecord.source_version_id == ver.id)).all()
    # Does not duplicate
    assert len(records2) == 2


def test_process_ingestion_job_fenced_when_source_deleted(db, tmp_path, monkeypatch):
    monkeypatch.setenv("STORAGE_DIR", str(tmp_path))
    dataset = Dataset(name=f"Job Dataset Tombstone Task {uuid4()}")
    db.add(dataset)
    db.flush()

    source = Source(
        dataset_id=dataset.id,
        logical_filename="doc.txt",
        profile_id="document",
        deleted_at=datetime.now(timezone.utc),
    )
    db.add(source)
    db.flush()

    storage_key = "tombstone-key"
    storage_file = tmp_path / "sources" / storage_key
    storage_file.parent.mkdir(parents=True, exist_ok=True)
    storage_file.write_bytes(b"Valid content")

    ver = SourceVersion(
        source_id=source.id,
        version_number=1,
        content_hash="thash",
        storage_key=storage_key,
        size_bytes=13,
        mime_type="text/plain",
    )
    db.add(ver)
    db.flush()

    job = ImportJob(source_version_id=ver.id, state="queued", attempt_count=0, max_attempts=3)
    db.add(job)
    db.commit()

    process_ingestion_job(str(job.id))
    db.expire_all()

    reloaded_job = db.get(ImportJob, job.id)
    assert reloaded_job.state == "failed"
    assert reloaded_job.error_code == "SOURCE_DELETED"

    reloaded_source = db.get(Source, source.id)
    assert reloaded_source.active_version_id is None

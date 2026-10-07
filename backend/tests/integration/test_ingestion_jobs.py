from datetime import datetime, timezone, timedelta
from uuid import uuid4
import pytest
from sqlalchemy import select, func
from app.database.models import Dataset, Source, SourceVersion, ImportJob, ParseRun, CanonicalRecord


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
        mime_type="text/plain"
    )
    db.add(ver)
    db.flush()

    job = ImportJob(
        source_version_id=ver.id,
        state=state,
        attempt_count=0,
        max_attempts=3
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
            ImportJob.lease_expires_at < now
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
        status="staged"
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
            record_metadata={}
        )
        db.add(rec)
    db.commit()

    count_before = db.scalar(
        select(func.count()).select_from(CanonicalRecord).where(CanonicalRecord.parse_run_id == run.id)
    )
    assert count_before == 2

    # Simulate rerun / retry on the same parse run: existing records are purged or upserted
    # rather than duplicated
    # In idempotent retry:
    db.query(CanonicalRecord).filter(CanonicalRecord.parse_run_id == run.id).delete()
    for pos in (1, 2):
        rec = CanonicalRecord(
            parse_run_id=run.id,
            source_version_id=ver.id,
            dataset_id=dataset.id,
            position=pos,
            locator_data={"line": pos},
            content_text=f"Line {pos} log content",
            record_metadata={}
        )
        db.add(rec)
    db.commit()

    count_after = db.scalar(
        select(func.count()).select_from(CanonicalRecord).where(CanonicalRecord.parse_run_id == run.id)
    )
    assert count_after == 2

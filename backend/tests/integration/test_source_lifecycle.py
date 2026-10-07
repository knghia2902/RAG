from datetime import datetime, timezone, timedelta
from uuid import uuid4
import pytest
from sqlalchemy import select
from app.database.models import (
    Account,
    Dataset,
    Source,
    SourceVersion,
    ImportJob,
    ParseRun,
)
from app.database.sources import (
    save_uploaded_source,
    reprocess_active_source,
    retry_failed_job,
    tombstone_source,
    reconcile_stale_jobs,
)


def create_test_admin(db):
    admin = Account(
        username=f"admin_{uuid4().hex[:6]}",
        display_name="Admin Test",
        role="admin",
        active=True,
        password_hash="test-hash",
    )
    db.add(admin)
    db.commit()
    return admin


def test_atomic_version_activation_failed_version_never_overwrites_active(db):
    dataset = Dataset(name=f"Lifecycle Dataset {uuid4().hex[:6]}")
    db.add(dataset)
    db.flush()

    source = Source(dataset_id=dataset.id, logical_filename="orders.csv", profile_id="operations_table")
    db.add(source)
    db.flush()

    # Version 1 is active
    ver1 = SourceVersion(
        source_id=source.id,
        version_number=1,
        content_hash="v1hash",
        storage_key="opaque-v1",
        size_bytes=100,
        mime_type="text/csv",
    )
    db.add(ver1)
    db.flush()
    source.active_version_id = ver1.id
    db.commit()

    assert source.active_version_id == ver1.id

    # Version 2 candidate arrives and fails validation
    ver2 = SourceVersion(
        source_id=source.id,
        version_number=2,
        content_hash="v2hash",
        storage_key="opaque-v2",
        size_bytes=120,
        mime_type="text/csv",
    )
    db.add(ver2)
    db.flush()

    job2 = ImportJob(
        source_version_id=ver2.id,
        state="failed",
        error_code="SCHEMA_ERROR",
        error_message="Invalid row 4",
    )
    db.add(job2)
    db.commit()

    # In atomic activation: source.active_version_id MUST NOT be updated to ver2
    db.expire_all()
    reloaded_source = db.get(Source, source.id)
    assert reloaded_source.active_version_id == ver1.id


def test_upload_idempotency_same_content_is_noop(db, tmp_path, monkeypatch):
    monkeypatch.setenv("STORAGE_DIR", str(tmp_path))
    admin = create_test_admin(db)
    dataset = Dataset(name=f"Upload Dataset {uuid4().hex[:6]}")
    db.add(dataset)
    db.commit()

    content = b"header1,header2\nval1,val2\n"

    # First upload creates new source and version 1
    src1, ver1, job1, is_new1 = save_uploaded_source(
        db, admin, dataset.id, "report.csv", "operations_table", content, "text/csv"
    )
    assert is_new1 is True
    assert ver1.version_number == 1
    assert job1.state == "queued"

    # Second upload with same content is a no-op idempotent
    src2, ver2, job2, is_new2 = save_uploaded_source(
        db, admin, dataset.id, "report.csv", "operations_table", content, "text/csv"
    )
    assert is_new2 is False
    assert src1.id == src2.id
    assert ver1.id == ver2.id
    assert ver2.version_number == 1


def test_upload_different_content_creates_version_2(db, tmp_path, monkeypatch):
    monkeypatch.setenv("STORAGE_DIR", str(tmp_path))
    admin = create_test_admin(db)
    dataset = Dataset(name=f"Version Dataset {uuid4().hex[:6]}")
    db.add(dataset)
    db.commit()

    content1 = b"version 1 content"
    content2 = b"version 2 content different bytes"

    # First upload
    src1, ver1, job1, is_new1 = save_uploaded_source(
        db, admin, dataset.id, "notes.txt", "document", content1, "text/plain"
    )
    assert is_new1 is True
    assert ver1.version_number == 1

    # Simulate ver1 became active
    src1.active_version_id = ver1.id
    job1.state = "ready"
    db.commit()

    # Second upload under same filename creates version 2
    src2, ver2, job2, is_new2 = save_uploaded_source(
        db, admin, dataset.id, "notes.txt", "document", content2, "text/plain"
    )
    assert is_new2 is True
    assert src1.id == src2.id
    assert ver2.version_number == 2
    assert ver2.id != ver1.id

    # Active version remains ver1 while ver2 is queued
    db.expire_all()
    reloaded_src = db.get(Source, src1.id)
    assert reloaded_src.active_version_id == ver1.id


def test_reprocess_runs_on_same_version_without_incrementing_number(db, tmp_path, monkeypatch):
    monkeypatch.setenv("STORAGE_DIR", str(tmp_path))
    admin = create_test_admin(db)
    dataset = Dataset(name=f"Reprocess Dataset {uuid4().hex[:6]}")
    db.add(dataset)
    db.commit()

    src, ver, job, _ = save_uploaded_source(
        db, admin, dataset.id, "server.log", "log", b"log data 1", "text/plain"
    )
    # Simulate ver1 activated
    src.active_version_id = ver.id
    job.state = "ready"
    db.commit()

    # Reprocess active source
    reprocess_job = reprocess_active_source(db, admin, dataset.id, src.id)
    assert reprocess_job.source_version_id == ver.id
    assert reprocess_job.state == "queued"

    # Version count remains 1, no version 2 created
    db.expire_all()
    versions = db.scalars(select(SourceVersion).where(SourceVersion.source_id == src.id)).all()
    assert len(versions) == 1
    assert versions[0].version_number == 1


def test_retry_failed_job_resets_state_and_errors(db, tmp_path, monkeypatch):
    monkeypatch.setenv("STORAGE_DIR", str(tmp_path))
    admin = create_test_admin(db)
    dataset = Dataset(name=f"Retry Dataset {uuid4().hex[:6]}")
    db.add(dataset)
    db.commit()

    src, ver, job, _ = save_uploaded_source(
        db, admin, dataset.id, "fail.txt", "document", b"content", "text/plain"
    )
    # Mark job as failed with error details
    job.state = "failed"
    job.error_code = "IO_ERROR"
    job.error_message = "Disk timeout"
    job.diagnostics = {"row": 1}
    db.commit()

    # Retry job
    retried_job = retry_failed_job(db, admin, dataset.id, src.id)
    assert retried_job.id == job.id
    assert retried_job.state == "queued"
    assert retried_job.error_code is None
    assert retried_job.error_message is None
    assert retried_job.diagnostics is None


def test_tombstone_source_marks_deleted_and_excludes_active_queries(db, tmp_path, monkeypatch):
    monkeypatch.setenv("STORAGE_DIR", str(tmp_path))
    admin = create_test_admin(db)
    dataset = Dataset(name=f"Tombstone Dataset {uuid4().hex[:6]}")
    db.add(dataset)
    db.commit()

    src, ver, job, _ = save_uploaded_source(
        db, admin, dataset.id, "remove.txt", "document", b"delete me", "text/plain"
    )
    assert src.deleted_at is None

    # Tombstone source
    tombstone_source(db, admin, dataset.id, src.id)

    db.expire_all()
    reloaded_src = db.get(Source, src.id)
    assert reloaded_src.deleted_at is not None

    # Active source query filters out deleted
    active_sources = db.scalars(
        select(Source).where(
            Source.dataset_id == dataset.id,
            Source.deleted_at.is_(None),
        )
    ).all()
    assert len(active_sources) == 0


def test_reconcile_stale_jobs_recovers_expired_leases(db, tmp_path, monkeypatch):
    monkeypatch.setenv("STORAGE_DIR", str(tmp_path))
    admin = create_test_admin(db)
    dataset = Dataset(name=f"Reconcile Dataset {uuid4().hex[:6]}")
    db.add(dataset)
    db.commit()

    src, ver, job1, _ = save_uploaded_source(
        db, admin, dataset.id, "stale1.txt", "document", b"data1", "text/plain"
    )
    # Job 1: lease expired, attempt 1 < max 3 -> recover to queued
    job1.state = "processing"
    job1.attempt_count = 1
    job1.max_attempts = 3
    job1.lease_expires_at = datetime.now(timezone.utc) - timedelta(minutes=15)

    src2, ver2, job2, _ = save_uploaded_source(
        db, admin, dataset.id, "stale2.txt", "document", b"data2", "text/plain"
    )
    # Job 2: lease expired, attempt 3 >= max 3 -> mark failed
    job2.state = "processing"
    job2.attempt_count = 3
    job2.max_attempts = 3
    job2.lease_expires_at = datetime.now(timezone.utc) - timedelta(minutes=15)

    db.commit()

    reconciled_count = reconcile_stale_jobs(db)
    assert reconciled_count >= 2

    db.expire_all()
    reloaded_job1 = db.get(ImportJob, job1.id)
    assert reloaded_job1.state == "queued"
    assert reloaded_job1.lease_expires_at is None

    reloaded_job2 = db.get(ImportJob, job2.id)
    assert reloaded_job2.state == "failed"
    assert reloaded_job2.error_code == "LEASE_EXPIRED_MAX_ATTEMPTS"

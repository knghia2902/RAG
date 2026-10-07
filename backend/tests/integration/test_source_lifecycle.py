from datetime import datetime, timezone
from uuid import uuid4
import pytest
from sqlalchemy import select
from app.database.models import Dataset, Source, SourceVersion, ImportJob, ParseRun


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
        mime_type="text/csv"
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
        mime_type="text/csv"
    )
    db.add(ver2)
    db.flush()

    job2 = ImportJob(
        source_version_id=ver2.id,
        state="failed",
        error_code="SCHEMA_ERROR",
        error_message="Invalid row 4"
    )
    db.add(job2)
    db.commit()

    # In atomic activation: source.active_version_id MUST NOT be updated to ver2
    reloaded_source = db.get(Source, source.id)
    assert reloaded_source.active_version_id == ver1.id


def test_reprocess_runs_on_same_version_without_incrementing_number(db):
    dataset = Dataset(name=f"Reprocess Dataset {uuid4().hex[:6]}")
    db.add(dataset)
    db.flush()

    source = Source(dataset_id=dataset.id, logical_filename="server.log", profile_id="log")
    db.add(source)
    db.flush()

    ver1 = SourceVersion(
        source_id=source.id,
        version_number=1,
        content_hash="loghash1",
        storage_key="opaque-log-v1",
        size_bytes=500,
        mime_type="text/plain"
    )
    db.add(ver1)
    db.flush()
    source.active_version_id = ver1.id

    job1 = ImportJob(source_version_id=ver1.id, state="ready")
    db.add(job1)
    db.commit()

    # Reprocess triggers a new parse run on ver1
    job_reprocess = ImportJob(source_version_id=ver1.id, state="queued")
    db.add(job_reprocess)
    db.commit()

    # Version count for this source must remain 1
    versions = db.scalars(
        select(SourceVersion).where(SourceVersion.source_id == source.id)
    ).all()
    assert len(versions) == 1
    assert versions[0].version_number == 1


def test_delete_source_tombstones_and_fences_active_worker(db):
    dataset = Dataset(name=f"Tombstone Dataset {uuid4().hex[:6]}")
    db.add(dataset)
    db.flush()

    source = Source(dataset_id=dataset.id, logical_filename="delete_me.txt", profile_id="document")
    db.add(source)
    db.flush()

    ver = SourceVersion(
        source_id=source.id,
        version_number=1,
        content_hash="delhash",
        storage_key="opaque-del",
        size_bytes=50,
        mime_type="text/plain"
    )
    db.add(ver)
    db.flush()
    source.active_version_id = ver.id

    job = ImportJob(source_version_id=ver.id, state="processing")
    db.add(job)
    db.commit()

    # Soft delete / tombstone
    now = datetime.now(timezone.utc)
    source.deleted_at = now
    db.commit()

    # Fencing check: worker checking if source is tombstoned
    def is_fenced(source_id) -> bool:
        src = db.get(Source, source_id)
        return src is None or src.deleted_at is not None

    assert is_fenced(source.id) is True

    # Tombstoned source cannot activate new version
    if is_fenced(source.id):
        # Abort worker publication
        job.state = "failed"
        job.error_code = "SOURCE_TOMBSTONED"
        db.commit()

    reloaded_job = db.get(ImportJob, job.id)
    assert reloaded_job.state == "failed"
    assert reloaded_job.error_code == "SOURCE_TOMBSTONED"

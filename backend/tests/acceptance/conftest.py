from datetime import datetime, timezone
from uuid import uuid4
import pytest
from app.auth.passwords import hash_password
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
from tests.conftest import HEADERS, PASSWORD


@pytest.fixture
def tech_user_and_dataset(db, client):
    """Create a technician user and a scoped logistics dataset with granted access."""
    username = f"tech_acc_{uuid4().hex[:6]}"
    tech = Account(
        username=username,
        display_name="Tech Acceptance",
        role="technician",
        password_hash=hash_password(PASSWORD),
    )
    dataset = Dataset(name=f"Logistics-Acceptance-{uuid4().hex[:8]}")
    db.add_all([tech, dataset])
    db.flush()

    grant = DatasetGrant(account_id=tech.id, dataset_id=dataset.id)
    db.add(grant)
    db.commit()

    # Log in as technician to get auth headers with CSRF token
    login_res = client.post(
        "/api/v1/auth/login",
        json={"username": username, "password": PASSWORD},
        headers=HEADERS,
    )
    assert login_res.status_code == 200, login_res.text
    tech_headers = {**HEADERS, "X-CSRF-Token": login_res.json()["csrf_token"]}

    return tech, dataset, tech_headers


@pytest.fixture
def logistics_source_version(db, tech_user_and_dataset):
    """Seed a valid Source, SourceVersion, ImportJob, and ParseRun for acceptance testing."""
    tech, dataset, tech_headers = tech_user_and_dataset

    source = Source(
        dataset_id=dataset.id,
        logical_filename="wms_acceptance.log",
        profile_id="text_log",
    )
    db.add(source)
    db.flush()

    version = SourceVersion(
        source_id=source.id,
        version_number=1,
        content_hash=f"hash_{uuid4().hex[:12]}",
        storage_key=f"storage_{uuid4().hex[:12]}",
        size_bytes=512,
        mime_type="text/plain",
    )
    db.add(version)
    db.flush()
    source.active_version_id = version.id

    job = ImportJob(source_version_id=version.id, state="ready")
    db.add(job)
    db.flush()

    run = ParseRun(
        source_version_id=version.id,
        job_id=job.id,
        parser_name="text_log",
        parser_version="1.0",
        status="published",
    )
    db.add(run)
    db.commit()

    return source, version, run

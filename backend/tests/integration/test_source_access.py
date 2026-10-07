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
from app.auth.passwords import hash_password
from tests.conftest import HEADERS, PASSWORD


def create_permitted_technician(db, dataset):
    tech = Account(
        username=f"access-tech-{uuid4().hex[:6]}",
        display_name="Access Tech",
        role="technician",
        password_hash=hash_password(PASSWORD)
    )
    db.add(tech)
    db.flush()
    db.add(DatasetGrant(account_id=tech.id, dataset_id=dataset.id))
    db.commit()
    return tech


def test_preview_source_granted_technician_allowed(client, db):
    dataset = Dataset(name=f"Access Dataset {uuid4().hex[:6]}")
    db.add(dataset)
    db.flush()

    source = Source(dataset_id=dataset.id, logical_filename="sop.txt", profile_id="document")
    db.add(source)
    db.flush()

    ver = SourceVersion(
        source_id=source.id,
        version_number=1,
        content_hash="hash1",
        storage_key="opaque-key-sop",
        size_bytes=200,
        mime_type="text/plain"
    )
    db.add(ver)
    db.flush()

    job = ImportJob(source_version_id=ver.id, state="ready")
    db.add(job)
    db.flush()

    parse_run = ParseRun(
        source_version_id=ver.id,
        job_id=job.id,
        parser_name="TextLogParser",
        parser_version="1.0.0",
        status="published"
    )
    db.add(parse_run)
    db.flush()

    record = CanonicalRecord(
        parse_run_id=parse_run.id,
        source_version_id=ver.id,
        dataset_id=dataset.id,
        position=1,
        locator_data={"line_start": 1, "line_end": 10, "page": 1},
        content_text="Quy trình xử lý sự cố TMS",
        record_metadata={"category": "sop"},
    )
    db.add(record)
    source.active_version_id = ver.id
    db.commit()

    tech = create_permitted_technician(db, dataset)
    login_resp = client.post(
        "/api/v1/auth/login",
        json={"username": tech.username, "password": PASSWORD},
        headers=HEADERS
    )
    assert login_resp.status_code == 200

    resp = client.get(f"/api/v1/datasets/{dataset.id}/sources/{source.id}/preview")
    assert resp.status_code == 200
    data = resp.json()
    assert data["source_id"] == str(source.id)
    assert data["version_number"] == 1
    assert data["total"] == 1
    assert len(data["items"]) == 1
    assert data["items"][0]["text"] == "Quy trình xử lý sự cố TMS"
    assert data["items"][0]["locator"]["line_start"] == 1
    assert data["items"][0]["locator"]["page"] == 1
    assert data["items"][0]["locator"]["source_version"] == 1


def test_preview_source_ungranted_technician_returns_404(client, db):
    dataset = Dataset(name=f"Ungranted Dataset {uuid4().hex[:6]}")
    db.add(dataset)
    db.flush()

    source = Source(dataset_id=dataset.id, logical_filename="private.txt", profile_id="document")
    db.add(source)
    db.commit()

    tech = Account(
        username=f"no-grant-{uuid4().hex[:6]}",
        display_name="No Grant",
        role="technician",
        password_hash=hash_password(PASSWORD)
    )
    db.add(tech)
    db.commit()

    client.post("/api/v1/auth/login", json={"username": tech.username, "password": PASSWORD}, headers=HEADERS)
    resp = client.get(f"/api/v1/datasets/{dataset.id}/sources/{source.id}/preview")
    # Technicians without grants must receive 404 (indistinguishable from missing dataset)
    assert resp.status_code == 404


def test_preview_recheck_response_revocation_returns_403(client, db, monkeypatch):
    dataset = Dataset(name=f"Revoke Dataset {uuid4().hex[:6]}")
    db.add(dataset)
    db.flush()

    source = Source(dataset_id=dataset.id, logical_filename="revoked.txt", profile_id="document")
    db.add(source)
    db.flush()

    ver = SourceVersion(
        source_id=source.id,
        version_number=1,
        content_hash="hash_rev",
        storage_key="opaque-key-rev",
        size_bytes=200,
        mime_type="text/plain"
    )
    db.add(ver)
    db.flush()
    source.active_version_id = ver.id
    db.commit()

    tech = create_permitted_technician(db, dataset)
    client.post("/api/v1/auth/login", json={"username": tech.username, "password": PASSWORD}, headers=HEADERS)

    # Simulate mid-request revocation: initial check succeeds, recheck_response finds revoked scope
    monkeypatch.setattr("app.database.datasets.allowed_dataset_ids", lambda db_sess, acct: set())

    resp = client.get(f"/api/v1/datasets/{dataset.id}/sources/{source.id}/preview")
    assert resp.status_code == 403
    assert "thay đổi" in resp.json()["detail"]


def test_preview_response_contains_no_internal_storage_paths(client, admin, db):
    dataset = Dataset(name=f"Path Leaks Dataset {uuid4().hex[:6]}")
    db.add(dataset)
    db.flush()

    source = Source(dataset_id=dataset.id, logical_filename="report.pdf", profile_id="document")
    db.add(source)
    db.flush()

    ver = SourceVersion(
        source_id=source.id,
        version_number=1,
        content_hash="sha256hash",
        storage_key="app_storage_sources_internal_key.pdf",
        size_bytes=4096,
        mime_type="application/pdf"
    )
    db.add(ver)
    db.flush()
    source.active_version_id = ver.id
    db.commit()

    resp = client.get(f"/api/v1/datasets/{dataset.id}/sources/{source.id}/preview", headers=admin)
    assert resp.status_code == 200, f"Got {resp.status_code}: {resp.text}"
    content = resp.text
    assert "app_storage_sources_internal_key" not in content
    assert "/app/storage" not in content


def test_list_source_profiles_accessible_and_scoped(client, db):
    dataset = Dataset(name=f"Profiles Dataset {uuid4().hex[:6]}")
    db.add(dataset)
    db.commit()

    tech = create_permitted_technician(db, dataset)
    client.post("/api/v1/auth/login", json={"username": tech.username, "password": PASSWORD}, headers=HEADERS)

    resp = client.get(f"/api/v1/datasets/{dataset.id}/sources/profiles")
    assert resp.status_code == 200
    profiles = resp.json()
    assert len(profiles) == 5
    profile_ids = {p["id"] for p in profiles}
    assert profile_ids == {"document", "log", "ticket", "incident", "operations_table"}

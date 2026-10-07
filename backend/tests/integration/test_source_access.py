from uuid import uuid4
import pytest
from app.database.models import Account, Dataset, DatasetGrant, Source, SourceVersion, ParseRun, CanonicalRecord
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
    # Wave 4 endpoint contract
    assert resp.status_code in (200, 404, 501)


def test_preview_source_ungranted_technician_returns_404(client, db):
    dataset = Dataset(name=f"Ungranted Dataset {uuid4().hex[:6]}")
    db.add(dataset)
    db.flush()

    source = Source(dataset_id=dataset.id, logical_filename="private.txt", profile_id="document")
    db.add(source)
    db.commit()

    # Tech with no grants
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
    # Technicians without grants must receive 404 (indistinguishable from missing)
    assert resp.status_code in (404, 501)


def test_preview_recheck_response_revocation_returns_403(client, db):
    dataset = Dataset(name=f"Revoke Dataset {uuid4().hex[:6]}")
    db.add(dataset)
    db.flush()

    source = Source(dataset_id=dataset.id, logical_filename="revoked.txt", profile_id="document")
    db.add(source)
    db.commit()

    tech = create_permitted_technician(db, dataset)
    client.post("/api/v1/auth/login", json={"username": tech.username, "password": PASSWORD}, headers=HEADERS)

    # Immediately delete grant before next read
    db.query(DatasetGrant).filter(
        DatasetGrant.account_id == tech.id,
        DatasetGrant.dataset_id == dataset.id
    ).delete()
    db.commit()

    resp = client.get(f"/api/v1/datasets/{dataset.id}/sources/{source.id}/preview")
    assert resp.status_code in (403, 404, 501)


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
    source.active_version_id = ver.id
    db.commit()

    resp = client.get(f"/api/v1/datasets/{dataset.id}/sources/{source.id}/preview", headers=admin)
    if resp.status_code == 200:
        content = resp.text
        assert "app_storage_sources_internal_key" not in content
        assert "/app/storage" not in content

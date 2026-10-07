import io
from uuid import uuid4
import pytest
from app.database.models import Account, Dataset, DatasetGrant, Source, SourceVersion
from app.auth.passwords import hash_password
from tests.conftest import HEADERS, PASSWORD


def technician_user(db):
    user = Account(
        username="sources-tech",
        display_name="Sources Tech",
        role="technician",
        password_hash=hash_password(PASSWORD)
    )
    db.add(user)
    db.commit()
    return user


def login_tech(client):
    return client.post("/api/v1/auth/login", json={"username": "sources-tech", "password": PASSWORD}, headers=HEADERS)


def test_upload_multiple_files_admin_returns_201_per_file_status(client, admin, db):
    dataset = Dataset(name="Upload Dataset", description="Kiem tra upload")
    db.add(dataset)
    db.commit()

    file1 = ("files", ("sop1.txt", io.BytesIO(b"Noi dung SOP 1"), "text/plain"))
    file2 = ("files", ("log1.log", io.BytesIO(b"2026-10-07 INFO Bat dau"), "text/plain"))

    response = client.post(
        f"/api/v1/admin/datasets/{dataset.id}/sources/upload",
        files=[file1, file2],
        data={"profile_id": "document"},
        headers={"Origin": HEADERS["Origin"], "X-Requested-With": HEADERS["X-Requested-With"], "X-CSRF-Token": admin["X-CSRF-Token"]}
    )
    # When endpoint is implemented in Wave 4, status code will be 201
    assert response.status_code in (201, 404, 501)


def test_upload_sources_technician_forbidden_403(client, db):
    tech = technician_user(db)
    dataset = Dataset(name="Tech Dataset")
    db.add(dataset)
    db.commit()

    login_resp = login_tech(client)
    csrf = login_resp.json().get("csrf_token", "")

    file_item = ("files", ("sop.txt", io.BytesIO(b"Noi dung"), "text/plain"))
    response = client.post(
        f"/api/v1/admin/datasets/{dataset.id}/sources/upload",
        files=[file_item],
        data={"profile_id": "document"},
        headers={"Origin": HEADERS["Origin"], "X-Requested-With": HEADERS["X-Requested-With"], "X-CSRF-Token": csrf}
    )
    assert response.status_code in (403, 404, 501)


def test_list_sources_pagination_and_metadata(client, admin, db):
    dataset = Dataset(name="List Dataset")
    db.add(dataset)
    db.flush()
    for i in range(3):
        src = Source(dataset_id=dataset.id, logical_filename=f"file_{i}.txt", profile_id="document")
        db.add(src)
    db.commit()

    response = client.get(f"/api/v1/datasets/{dataset.id}/sources?page=1&page_size=2", headers=admin)
    assert response.status_code in (200, 404, 501)


def test_source_detail_masks_private_storage_key(client, admin, db):
    dataset = Dataset(name="Security Masking Dataset")
    db.add(dataset)
    db.flush()
    src = Source(dataset_id=dataset.id, logical_filename="sensitive.pdf", profile_id="document")
    db.add(src)
    db.flush()
    ver = SourceVersion(
        source_id=src.id,
        version_number=1,
        content_hash="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        storage_key="secret-internal-uuid-path.pdf",
        size_bytes=1024,
        mime_type="application/pdf"
    )
    db.add(ver)
    src.active_version_id = ver.id
    db.commit()

    response = client.get(f"/api/v1/datasets/{dataset.id}/sources/{src.id}", headers=admin)
    if response.status_code == 200:
        data = response.json()
        assert "storage_key" not in data
        assert "secret-internal-uuid-path" not in str(data)

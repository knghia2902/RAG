import io
from uuid import uuid4
import pytest
from app.database.models import Account, Dataset, DatasetGrant, Source, SourceVersion, ImportJob
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
    file2 = ("files", ("sop2.txt", io.BytesIO(b"Noi dung SOP 2"), "text/plain"))

    response = client.post(
        f"/api/v1/admin/datasets/{dataset.id}/sources/upload",
        files=[file1, file2],
        data={"profile_id": "document"},
        headers={"Origin": HEADERS["Origin"], "X-Requested-With": HEADERS["X-Requested-With"], "X-CSRF-Token": admin["X-CSRF-Token"]}
    )
    assert response.status_code == 201
    data = response.json()
    assert len(data["items"]) == 2
    assert data["items"][0]["filename"] == "sop1.txt"
    assert data["items"][0]["version_number"] == 1
    assert data["items"][0]["is_duplicate"] is False
    assert data["items"][1]["filename"] == "sop2.txt"
    assert data["items"][1]["version_number"] == 1
    assert data["items"][1]["is_duplicate"] is False

    # Second upload with identical file1 -> idempotent duplicate notification
    file1_dup = ("files", ("sop1.txt", io.BytesIO(b"Noi dung SOP 1"), "text/plain"))
    response_dup = client.post(
        f"/api/v1/admin/datasets/{dataset.id}/sources/upload",
        files=[file1_dup],
        data={"profile_id": "document"},
        headers={"Origin": HEADERS["Origin"], "X-Requested-With": HEADERS["X-Requested-With"], "X-CSRF-Token": admin["X-CSRF-Token"]}
    )
    assert response_dup.status_code == 201
    data_dup = response_dup.json()
    assert len(data_dup["items"]) == 1
    assert data_dup["items"][0]["is_duplicate"] is True
    assert "trùng lặp" in data_dup["items"][0]["message"]


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
    assert response.status_code == 403


def test_technician_forbidden_on_all_mutations(client, admin, db):
    tech = technician_user(db)
    dataset = Dataset(name="Mutation Auth Dataset")
    db.add(dataset)
    db.flush()

    source = Source(dataset_id=dataset.id, logical_filename="test.txt", profile_id="document")
    db.add(source)
    db.flush()
    ver = SourceVersion(
        source_id=source.id,
        version_number=1,
        content_hash="hash1",
        storage_key="test-key",
        size_bytes=100,
        mime_type="text/plain"
    )
    db.add(ver)
    db.flush()
    source.active_version_id = ver.id

    job = ImportJob(source_version_id=ver.id, state="failed", error_message="Loi parse")
    db.add(job)
    db.commit()

    login_resp = login_tech(client)
    csrf = login_resp.json().get("csrf_token", "")
    tech_headers = {**HEADERS, "X-CSRF-Token": csrf}

    # Retry forbidden for technician
    retry_resp = client.post(f"/api/v1/admin/datasets/{dataset.id}/sources/{source.id}/retry", headers=tech_headers)
    assert retry_resp.status_code == 403

    # Reprocess forbidden for technician
    reprocess_resp = client.post(f"/api/v1/admin/datasets/{dataset.id}/sources/{source.id}/reprocess", headers=tech_headers)
    assert reprocess_resp.status_code == 403

    # Delete forbidden for technician
    delete_resp = client.delete(f"/api/v1/admin/datasets/{dataset.id}/sources/{source.id}", headers=tech_headers)
    assert delete_resp.status_code == 403


def test_admin_retry_reprocess_delete_lifecycle(client, admin, db):
    dataset = Dataset(name="Admin Lifecycle Dataset")
    db.add(dataset)
    db.flush()

    source = Source(dataset_id=dataset.id, logical_filename="sop.txt", profile_id="document")
    db.add(source)
    db.flush()
    ver = SourceVersion(
        source_id=source.id,
        version_number=1,
        content_hash="hash_lc",
        storage_key="key_lc",
        size_bytes=100,
        mime_type="text/plain"
    )
    db.add(ver)
    db.flush()
    source.active_version_id = ver.id

    job = ImportJob(source_version_id=ver.id, state="failed", error_message="Loi thu nghiem")
    db.add(job)
    db.commit()

    admin_headers = {**HEADERS, "X-CSRF-Token": admin["X-CSRF-Token"]}

    # Admin retry
    retry_resp = client.post(f"/api/v1/admin/datasets/{dataset.id}/sources/{source.id}/retry", headers=admin_headers)
    assert retry_resp.status_code == 200
    assert retry_resp.json()["state"] == "queued"

    # Admin reprocess
    reprocess_resp = client.post(f"/api/v1/admin/datasets/{dataset.id}/sources/{source.id}/reprocess", headers=admin_headers)
    assert reprocess_resp.status_code == 200
    assert reprocess_resp.json()["state"] == "queued"

    # Admin delete (tombstone)
    del_resp = client.delete(f"/api/v1/admin/datasets/{dataset.id}/sources/{source.id}", headers=admin_headers)
    assert del_resp.status_code == 200

    # Source should now return 404
    detail_resp = client.get(f"/api/v1/datasets/{dataset.id}/sources/{source.id}", headers=admin)
    assert detail_resp.status_code == 404


def test_upload_format_and_batch_limits(client, admin, db):
    dataset = Dataset(name="Limits Dataset")
    db.add(dataset)
    db.commit()

    admin_headers = {"Origin": HEADERS["Origin"], "X-Requested-With": HEADERS["X-Requested-With"], "X-CSRF-Token": admin["X-CSRF-Token"]}

    # Unsupported format for document profile (.exe)
    bad_file = ("files", ("malicious.exe", io.BytesIO(b"MZ..."), "application/octet-stream"))
    resp = client.post(
        f"/api/v1/admin/datasets/{dataset.id}/sources/upload",
        files=[bad_file],
        data={"profile_id": "document"},
        headers=admin_headers,
    )
    assert resp.status_code == 400
    assert "không được hỗ trợ" in resp.json()["detail"]

    # Batch > 10 files
    too_many = [("files", (f"file_{i}.txt", io.BytesIO(b"test"), "text/plain")) for i in range(11)]
    resp_limit = client.post(
        f"/api/v1/admin/datasets/{dataset.id}/sources/upload",
        files=too_many,
        data={"profile_id": "document"},
        headers=admin_headers,
    )
    assert resp_limit.status_code == 400
    assert "tối đa" in resp_limit.json()["detail"]


def test_list_sources_pagination_and_metadata(client, admin, db):
    dataset = Dataset(name="List Dataset")
    db.add(dataset)
    db.flush()
    for i in range(3):
        src = Source(dataset_id=dataset.id, logical_filename=f"file_{i}.txt", profile_id="document")
        db.add(src)
    db.commit()

    response = client.get(f"/api/v1/datasets/{dataset.id}/sources?page=1&page_size=2", headers=admin)
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 3
    assert len(data["items"]) == 2
    assert data["page"] == 1
    assert data["page_size"] == 2


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
    assert response.status_code == 200
    data = response.json()
    assert "storage_key" not in data
    assert "secret-internal-uuid-path" not in str(data)

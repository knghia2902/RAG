from uuid import uuid4
from unittest.mock import patch
from fastapi.testclient import TestClient
from sqlalchemy import select, delete
from app.database.models import Account, Dataset, DatasetGrant
from app.database.session import SessionLocal
from app.auth.passwords import hash_password
from tests.conftest import HEADERS, PASSWORD


def technician(db):
    row = Account(username="acl-tech", display_name="Tech", role="technician", password_hash=hash_password(PASSWORD))
    db.add(row); db.commit()
    return row


def login(client):
    return client.post("/api/v1/auth/login", json={"username":"acl-tech", "password":PASSWORD}, headers=HEADERS)


def test_metadata_admin_validation_and_rollback(client, admin, db):
    result = client.post("/api/v1/admin/datasets", json={"name":"WMS", "description":"Nguồn vận hành"}, headers=admin)
    assert result.status_code == 201
    path = f"/api/v1/admin/datasets/{result.json()['id']}"
    assert client.patch(path, json={"description":"Updated"}, headers=admin).json()["description"] == "Updated"
    assert client.post("/api/v1/admin/datasets", json={"name":"WMS"}, headers=admin).status_code == 409
    for payload in ({"name":""}, {"name":"x"*129}, {"name":"ok", "description":"x"*2001}, {"name":"ok", "extra":True}):
        assert client.post("/api/v1/admin/datasets", json=payload, headers=admin).status_code == 422
    with patch.object(SessionLocal.class_, "commit", side_effect=RuntimeError("Injected failure")):
        assert client.patch(path, json={"name":"Changed"}, headers=admin).status_code == 503
    assert client.get(path.replace("/admin", "")).json()["name"] == "WMS"
    assert client.post("/api/v1/admin/datasets", json={"name":"No CSRF"}, headers=HEADERS).status_code == 403


def test_current_acl_count_detail_and_zero_default(client, admin, db):
    tech = technician(db)
    rows = [Dataset(name=f"Dataset {i}") for i in range(3)]
    db.add_all(rows); db.commit()
    login(client)
    assert client.get("/api/v1/datasets").json()["total"] == 0
    assert client.post("/api/v1/admin/datasets", json={"name":"denied"}, headers={**HEADERS,"X-CSRF-Token":login(client).json()["csrf_token"]}).status_code == 403
    hidden = client.get(f"/api/v1/datasets/{rows[0].id}")
    missing = client.get(f"/api/v1/datasets/{uuid4()}")
    assert hidden.status_code == missing.status_code == 404 and hidden.json() == missing.json()
    db.add(DatasetGrant(account_id=tech.id,dataset_id=rows[1].id)); db.commit()
    page = client.get("/api/v1/datasets?page_size=1").json()
    assert page["total"] == 1 and [r["id"] for r in page["items"]] == [str(rows[1].id)]
    assert client.get(f"/api/v1/datasets/{rows[1].id}").status_code == 200
    for query in ("page=0", "page_size=101", "page_size=0"):
        assert client.get(f"/api/v1/datasets?{query}").status_code == 422
    assert client.get("/api/v1/datasets/not-uuid").status_code == 422


def test_revoke_after_lookup_before_response(client, admin, db):
    tech = technician(db); row = Dataset(name="Sensitive WMS")
    db.add(row); db.flush(); db.add(DatasetGrant(account_id=tech.id,dataset_id=row.id)); db.commit()
    login(client)
    assert client.get(f"/api/v1/datasets/{row.id}").status_code == 200
    from app.database import datasets
    original = datasets.recheck_response
    def revoke(*args, **kwargs):
        with SessionLocal.begin() as other:
            other.execute(delete(DatasetGrant).where(DatasetGrant.account_id==tech.id))
        return original(*args, **kwargs)
    with patch.object(datasets, "recheck_response", side_effect=revoke):
        response = client.get(f"/api/v1/datasets/{row.id}")
    assert response.status_code == 404 and row.name not in response.text
    db.add(DatasetGrant(account_id=tech.id,dataset_id=row.id)); db.commit()
    with patch.object(datasets, "recheck_response", side_effect=revoke):
        response = client.get("/api/v1/datasets")
    assert response.status_code == 403 and row.name not in response.text and "total" not in response.text

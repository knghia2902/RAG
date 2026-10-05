from uuid import uuid4
from unittest.mock import patch
from fastapi.testclient import TestClient
from sqlalchemy import select, delete
from app.database.models import Account, Dataset, DatasetGrant
from app.database.session import SessionLocal
from app.auth.passwords import hash_password
from tests.conftest import HEADERS, PASSWORD
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier, Event, local
import pytest


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


def test_grants_idempotent_safe_targets_live_session_and_rollback(client, admin, db, caplog):
    from app.main import app
    tech=technician(db); rows=[Dataset(name=f"Grant {i}") for i in range(2)]
    db.add_all(rows); db.commit()
    path=f"/api/v1/admin/users/{tech.id}/datasets"
    assert client.get(path).status_code==200
    assert client.get(path).json()=={"dataset_ids":[]}
    with TestClient(app,base_url="http://next-test:3000") as second:
        login(second)
        for _ in range(2):
            assert client.put(f"{path}/{rows[0].id}",json={},headers=admin).status_code==200
        assert second.get("/api/v1/datasets").json()["total"]==1
        with patch.object(SessionLocal.class_,"commit",side_effect=RuntimeError("Injected failure")):
            assert client.delete(f"{path}/{rows[0].id}",headers=admin).status_code==503
        assert second.get("/api/v1/datasets").json()["total"]==1
        for _ in range(2):
            assert client.delete(f"{path}/{rows[0].id}",headers=admin).status_code==200
        assert second.get(f"/api/v1/datasets/{rows[0].id}").status_code==404
        assert second.get("/api/v1/datasets").json()["total"]==0
        assert second.get(path).status_code==403
    actor=db.scalar(select(Account).where(Account.role=="admin"))
    assert client.put(f"/api/v1/admin/users/{actor.id}/datasets/{rows[0].id}",json={},headers=admin).status_code==404
    assert client.put(f"{path}/{uuid4()}",json={},headers=admin).status_code==404
    assert client.put(f"{path}/{rows[0].id}",json={},headers=HEADERS).status_code==403
    assert "dataset.grant" in caplog.text and "dataset.revoke" in caplog.text and PASSWORD not in caplog.text


def test_independent_connection_grant_races(client, admin, db):
    from app.main import app
    tech=technician(db); rows=[Dataset(name=f"Race {i}") for i in range(2)]
    db.add_all(rows); db.commit();path=f"/api/v1/admin/users/{tech.id}/datasets"
    def race(operations):
        barrier=Barrier(len(operations))
        def write(operation):
            method, dataset_id=operation
            with TestClient(app,base_url="http://next-test:3000") as caller:
                response=caller.post("/api/v1/auth/login",json={"username":"admin","password":PASSWORD},headers=HEADERS)
                headers={**HEADERS,"X-CSRF-Token":response.json()["csrf_token"]}
                barrier.wait(timeout=10)
                return caller.request(method,f"{path}/{dataset_id}",json={},headers=headers).status_code
        with ThreadPoolExecutor(max_workers=len(operations)) as pool:
            assert list(pool.map(write,operations))==[200]*len(operations)
    race([("PUT",rows[0].id)]*2)
    assert client.get(path).json()["dataset_ids"]==[str(rows[0].id)]
    race([("DELETE",rows[0].id)]*2)
    assert client.get(path).json()["dataset_ids"]==[]
    race([("PUT",row.id) for row in rows])
    assert set(client.get(path).json()["dataset_ids"])=={str(row.id) for row in rows}
    race([("DELETE",rows[0].id),("PUT",rows[0].id)])
    ids=client.get(path).json()["dataset_ids"]
    assert str(rows[1].id) in ids and len(ids)==len(set(ids))


@pytest.mark.parametrize("first,second",[("PUT","DELETE"),("DELETE","PUT")])
def test_opposing_grants_follow_serialized_commit_order(client,admin,db,first,second):
    from app.main import app
    tech=technician(db);row=Dataset(name="Ordered grant")
    db.add(row);db.flush();db.add(DatasetGrant(account_id=tech.id,dataset_id=row.id));db.commit()
    path=f"/api/v1/admin/users/{tech.id}/datasets/{row.id}"
    callers=[TestClient(app,base_url="http://next-test:3000") for _ in range(2)]
    headers=[]
    for caller in callers:
        response=caller.post("/api/v1/auth/login",json={"username":"admin","password":PASSWORD},headers=HEADERS)
        headers.append({**HEADERS,"X-CSRF-Token":response.json()["csrf_token"]})
    ready,release,second_started=Event(),Event(),Event();thread=local();original=SessionLocal.class_.commit
    from app.database import datasets
    original_grant=datasets.set_grant
    def set_grant(*args):
        thread.hold=args[-1]==(first=="PUT")
        try:return original_grant(*args)
        finally:thread.hold=False
    def commit(session):
        if getattr(thread,"hold",False):
            ready.set();assert release.wait(timeout=10)
        return original(session)
    def write(index,method):
        if index==1:second_started.set()
        return callers[index].request(method,path,json={},headers=headers[index]).status_code
    try:
        with patch.object(datasets,"set_grant",set_grant),patch.object(SessionLocal.class_,"commit",commit),ThreadPoolExecutor(max_workers=2) as pool:
            a=pool.submit(write,0,first);assert ready.wait(timeout=10)
            b=pool.submit(write,1,second);assert second_started.wait(timeout=10);release.set()
            assert a.result(timeout=10)==b.result(timeout=10)==200
        assert (str(row.id) in client.get(path.rsplit("/",1)[0]).json()["dataset_ids"])==(second=="PUT")
    finally:
        release.set()
        for caller in callers:caller.close()

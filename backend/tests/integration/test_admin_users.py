from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from unittest.mock import patch
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select, func
from app.database.models import Account, AuthSession
from app.database.session import SessionLocal
from app.auth.passwords import hash_password
from tests.conftest import HEADERS, PASSWORD


def test_admin_create_duplicate_safe_dto_and_metadata(client,admin,db):
    payload={"username":"NEW.TECH","display_name":"Nguyễn Văn A","role":"technician","temporary_password":PASSWORD}
    result=client.post("/api/v1/admin/users",json=payload,headers=admin)
    assert result.status_code==201
    data=result.json();assert data["username"]=="new.tech" and data["must_change_password"] is True
    assert PASSWORD not in result.text and "password_hash" not in result.text
    assert client.post("/api/v1/admin/users",json=payload,headers=admin).status_code==409
    assert client.patch(f"/api/v1/admin/users/{data['id']}",json={"username":"changed"},headers=admin).status_code==422
    result=client.patch(f"/api/v1/admin/users/{data['id']}",json={"display_name":"Tên mới"},headers=admin)
    assert result.status_code==200 and result.json()["display_name"]=="Tên mới"
    assert client.get("/api/v1/admin/users").json()["total"]==2


def test_self_demotion_disable_and_technician_denied(client,admin,db):
    actor=db.scalar(select(Account));path=f"/api/v1/admin/users/{actor.id}"
    for payload in ({"active":False},{"role":"technician"}):
        assert client.patch(path,json=payload,headers=admin).status_code==409
    tech=Account(username="technician",display_name="Tech",password_hash=hash_password(PASSWORD),role="technician")
    db.add(tech);db.commit()
    response=client.post("/api/v1/auth/login",json={"username":"technician","password":PASSWORD},headers=HEADERS)
    headers={**HEADERS,"X-CSRF-Token":response.json()["csrf_token"]}
    assert client.get("/api/v1/admin/users").status_code==403
    assert client.post("/api/v1/admin/users",json={"username":"bad","display_name":"Bad","role":"admin","temporary_password":PASSWORD},headers=headers).status_code==403


def test_reset_disable_revoke_and_failure_rolls_back(client,admin,db,caplog):
    from app.main import app
    target=Account(username="target",display_name="Target",password_hash=hash_password(PASSWORD),role="technician")
    db.add(target);db.commit();old_hash=target.password_hash
    with TestClient(app,base_url="http://next-test:3000") as second:
        second.post("/api/v1/auth/login",json={"username":"target","password":PASSWORD},headers=HEADERS)
        result=client.patch(f"/api/v1/admin/users/{target.id}",json={"display_name":"Target"},headers=admin)
        assert result.status_code==200 and second.get("/api/v1/auth/session").status_code==200
        with patch.object(SessionLocal.class_,"commit",side_effect=RuntimeError("Injected write failure")):
            response=client.post(f"/api/v1/admin/users/{target.id}/reset-password",json={"temporary_password":"changed-password-123456"},headers=admin)
            assert response.status_code==503
        db.refresh(target);assert target.password_hash==old_hash
        assert second.get("/api/v1/auth/session").status_code==200
        response=client.post(f"/api/v1/admin/users/{target.id}/reset-password",json={"temporary_password":"changed-password-123456"},headers=admin)
        assert response.status_code==200 and second.get("/api/v1/auth/session").status_code==401
        db.refresh(target);assert target.must_change_password
        second.post("/api/v1/auth/login",json={"username":"target","password":"changed-password-123456"},headers=HEADERS)
        assert second.get("/api/v1/auth/session").status_code==200
        assert client.patch(f"/api/v1/admin/users/{target.id}",json={"active":False},headers=admin).status_code==200
        assert second.get("/api/v1/auth/session").status_code==401
        assert "account.reset_password" in caplog.text
        assert PASSWORD not in caplog.text and "changed-password-123456" not in caplog.text


def test_independent_connections_concurrent_admin_mutations(db):
    from app.main import app
    actors=[Account(username=name,display_name=name,password_hash=hash_password(PASSWORD),role="admin") for name in ("admin-one","admin-two")]
    db.add_all(actors);db.commit();barrier=Barrier(2)
    def mutate(index):
        with TestClient(app,base_url="http://next-test:3000") as client:
            login=client.post("/api/v1/auth/login",json={"username":actors[index].username,"password":PASSWORD},headers=HEADERS)
            headers={**HEADERS,"X-CSRF-Token":login.json()["csrf_token"]}
            barrier.wait(timeout=10)
            return client.patch(f"/api/v1/admin/users/{actors[1-index].id}",json={"role":"technician"},headers=headers).status_code
    with ThreadPoolExecutor(max_workers=2) as pool:
        results=list(pool.map(mutate,[0,1]))
    assert 200 in results and all(code in (200,401,403,409) for code in results)
    assert db.scalar(select(func.count()).select_from(Account).where(Account.role=="admin",Account.active.is_(True)))==1

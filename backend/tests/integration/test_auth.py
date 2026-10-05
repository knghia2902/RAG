from sqlalchemy import select
from app.auth.sessions import digest
from app.database.models import Account, AuthSession, Dataset, DatasetGrant
from app.auth.passwords import hash_password
from tests.conftest import HEADERS, PASSWORD


def test_login_digest_logout_replay(client, admin, db):
    token = client.cookies.get("rag_session")
    row = db.scalar(select(AuthSession))
    assert row.token_digest == digest(token) and row.token_digest != token
    assert db.scalar(select(Account)).password_hash.startswith("$argon2id$")
    assert client.get("/api/v1/auth/session").status_code == 200
    assert client.get("/api/v1/datasets").json()["items"] == []
    assert client.post("/api/v1/auth/logout", json={}, headers=admin).status_code == 204
    assert client.get("/api/v1/datasets", headers={"Cookie":f"rag_session={token}"}).status_code == 401


def test_unsafe_requires_origin_json_and_csrf(client, admin):
    for headers, status in (({},403), ({**admin,"Origin":"http://evil.invalid"},403), ({**admin,"Host":"evil.invalid"},403), ({**admin,"X-CSRF-Token":"wrong"},403), ({**admin,"Content-Type":"text/plain"},415)):
        response=client.post("/api/v1/auth/logout", content="{}", headers=headers)
        assert response.status_code == status
    assert client.get("/api/v1/auth/session").status_code == 200


def test_dataset_acl_before_count(client, db):
    user=Account(username="tech",display_name="Kỹ thuật viên",password_hash=hash_password(PASSWORD),role="technician")
    allowed=Dataset(name="WMS",description="Visible")
    hidden=Dataset(name="Secret",description="Hidden")
    db.add_all([user,allowed,hidden]);db.flush()
    db.add(DatasetGrant(account_id=user.id,dataset_id=allowed.id));db.commit()
    login=client.post("/api/v1/auth/login",json={"username":"tech","password":PASSWORD},headers=HEADERS)
    assert login.status_code==200
    result=client.get("/api/v1/datasets").json()
    assert result["total"]==1 and [row["name"] for row in result["items"]]==["WMS"]
    assert "Secret" not in str(result)


def test_disabled_current_account_and_safe_validation(client,admin,db):
    response=client.post("/api/v1/auth/login",json={"username":"admin","password":"secret"},headers=HEADERS)
    assert response.status_code==422 and "secret" not in response.text
    user=db.scalar(select(Account));user.active=False;db.commit()
    assert client.get("/api/v1/auth/session").status_code==401


def test_passive_polling_activity_and_expiry(client,admin,db,monkeypatch):
    from datetime import timedelta
    from app.auth import sessions
    row=db.scalar(select(AuthSession));start=row.created_at
    monkeypatch.setattr(sessions,"now_utc",lambda:start+timedelta(minutes=20))
    for path in ("/api/v1/auth/session","/api/v1/datasets"):
        assert client.get(path).status_code==200
    db.refresh(row);assert row.last_activity_at==start
    assert client.post("/api/v1/auth/activity",json={},headers=admin).status_code==204
    db.refresh(row);assert row.last_activity_at==start+timedelta(minutes=20)
    monkeypatch.setattr(sessions,"now_utc",lambda:start+timedelta(minutes=50))
    assert client.post("/api/v1/auth/activity",json={},headers=admin).status_code==401
    assert client.get("/api/v1/auth/session").status_code==401


def test_activity_after_logout_cannot_revive(client,admin,db):
    token=client.cookies.get("rag_session")
    assert client.post("/api/v1/auth/logout",json={},headers=admin).status_code==204
    response=client.post("/api/v1/auth/activity",json={},headers={**admin,"Cookie":f"rag_session={token}"})
    assert response.status_code==401
    db.expire_all();row=db.scalar(select(AuthSession));assert row.revoked_at is not None


def test_stale_activity_snapshot_after_committed_revocation(client,admin,db):
    from fastapi import HTTPException
    import pytest
    from app.auth.sessions import record_activity, now_utc
    from app.database.session import SessionLocal
    from sqlalchemy import update
    stale=db.scalar(select(AuthSession))
    with SessionLocal.begin() as other:
        other.execute(update(AuthSession).where(AuthSession.id==stale.id).values(revoked_at=now_utc()))
    with pytest.raises(HTTPException) as error:
        record_activity(db,stale)
    assert error.value.status_code==401
    db.rollback();db.refresh(stale);assert stale.revoked_at is not None

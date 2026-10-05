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


def test_forced_password_rotation_preserves_absolute_deadline(client,admin,db,monkeypatch):
    from datetime import timedelta
    from app.auth import sessions
    user=db.scalar(select(Account));user.must_change_password=True;db.commit()
    old_token=client.cookies.get("rag_session");old_csrf=admin["X-CSRF-Token"];created=db.scalar(select(AuthSession)).created_at
    assert client.get("/api/v1/datasets").status_code==403
    assert client.get("/api/v1/admin/users").status_code==403
    assert client.post("/api/v1/auth/change-password",json={"current_password":PASSWORD,"new_password":PASSWORD},headers=admin).status_code==422
    monkeypatch.setattr(sessions,"now_utc",lambda:created+timedelta(minutes=10))
    response=client.post("/api/v1/auth/change-password",json={"current_password":PASSWORD,"new_password":"new-password-long-enough"},headers=admin)
    assert response.status_code==200
    assert client.cookies.get("rag_session")!=old_token and response.json()["csrf_token"]!=old_csrf
    current=db.scalar(select(AuthSession).where(AuthSession.token_digest==digest(client.cookies.get("rag_session"))))
    assert current.created_at==created
    assert client.get("/api/v1/datasets").status_code==200
    assert client.get("/api/v1/auth/session",headers={"Cookie":f"rag_session={old_token}"}).status_code==401
    assert client.post("/api/v1/auth/activity",json={},headers=admin).status_code==403


def test_login_limit_rolling_window_recovery_and_spoofed_ip(client,db,monkeypatch):
    from datetime import datetime,timedelta,timezone
    from app.auth import sessions
    start=datetime(2026,1,1,tzinfo=timezone.utc);monkeypatch.setattr(sessions,"now_utc",lambda:start)
    for index in range(5):
        response=client.post("/api/v1/auth/login",json={"username":"unknown","password":PASSWORD},headers={**HEADERS,"X-Forwarded-For":f"10.0.0.{index}"})
        assert response.status_code==401
    response=client.post("/api/v1/auth/login",json={"username":"other-user","password":PASSWORD},headers=HEADERS)
    assert response.status_code==429 and int(response.headers["Retry-After"])>0
    monkeypatch.setattr(sessions,"now_utc",lambda:start+timedelta(minutes=5))
    assert client.post("/api/v1/auth/login",json={"username":"unknown","password":PASSWORD},headers=HEADERS).status_code==401


def test_concurrent_login_failures_do_not_lose_counts(db):
    from concurrent.futures import ThreadPoolExecutor
    from fastapi.testclient import TestClient
    from app.main import app
    from app.database.models import LoginRateBucket
    from sqlalchemy import func
    def fail(index):
        with TestClient(app,base_url="http://next-test:3000") as client:
            return client.post("/api/v1/auth/login",json={"username":"unknown","password":PASSWORD},headers=HEADERS).status_code
    with ThreadPoolExecutor(max_workers=5) as pool:
        assert list(pool.map(fail,range(5)))==[401]*5
    assert db.scalar(select(func.count()).select_from(LoginRateBucket))==10
    assert fail(5)==429


def test_failure_timestamps_roll_individually(client,db,monkeypatch):
    from datetime import datetime,timedelta,timezone
    from app.auth import sessions
    start=datetime(2026,1,1,tzinfo=timezone.utc)
    def fail():return client.post("/api/v1/auth/login",json={"username":"unknown","password":PASSWORD},headers=HEADERS).status_code
    monkeypatch.setattr(sessions,"now_utc",lambda:start)
    assert [fail() for _ in range(3)]==[401]*3
    monkeypatch.setattr(sessions,"now_utc",lambda:start+timedelta(minutes=4))
    assert [fail() for _ in range(2)]==[401]*2
    assert fail()==429
    monkeypatch.setattr(sessions,"now_utc",lambda:start+timedelta(minutes=5))
    assert [fail() for _ in range(3)]==[401]*3
    assert fail()==429


def test_login_bucket_storage_is_bounded(client,db,monkeypatch):
    from app.auth import rate_limit
    from app.database.models import LoginRateBucket
    from sqlalchemy import func
    monkeypatch.setattr(rate_limit,"MAX_ROWS",4)
    def fail():return client.post("/api/v1/auth/login",json={"username":"unknown","password":PASSWORD},headers=HEADERS).status_code
    assert fail()==401 and fail()==429
    assert db.scalar(select(func.count()).select_from(LoginRateBucket))==2

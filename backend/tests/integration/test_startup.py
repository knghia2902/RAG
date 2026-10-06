from datetime import timedelta
from unittest.mock import patch
import os
import subprocess
import pytest
from pydantic import SecretStr
from sqlalchemy import select
from app.config import get_settings
from app.database.models import Account,AuthSession
from app.auth import sessions
from app.auth.passwords import hash_password
from tests.conftest import PASSWORD,HEADERS


def test_no_ai_key_startup_and_safe_status(client,admin,monkeypatch,caplog):
    sentinel="status-secret-sentinel-do-not-display"
    settings=get_settings()
    monkeypatch.setattr(settings,"openai_api_key",SecretStr(""))
    assert client.get("/health/live").json()=={"status":"live"}
    assert client.get("/health/ready").status_code==200
    assert client.get("/health").json()=={"database_ready":True}
    response=client.get("/api/v1/status")
    assert response.status_code==200,response.text
    assert response.json()=={"database_ready":True,"provider_configured":False}
    monkeypatch.setattr(settings,"openai_api_key",SecretStr(sentinel))
    response=client.get("/api/v1/status")
    assert response.json()=={"database_ready":True,"provider_configured":True}
    assert sentinel not in response.text+caplog.text
    assert response.headers["Cache-Control"]=="no-store"
    assert client.put("/api/v1/status",json={"openai_api_key":sentinel},headers=admin).status_code==405


def test_provider_free_fresh_process_import_and_health():
    env={**os.environ,"OPENAI_API_KEY":""}
    result=subprocess.run(["python","-c", "import sys; from app.main import app; assert not any(n == 'openai' or n.startswith('langchain') for n in sys.modules); from fastapi.testclient import TestClient; c=TestClient(app); assert c.get('/health').status_code==200"],env=env,capture_output=True,text=True)
    assert result.returncode==0,result.stderr


def test_status_current_role_forced_password_and_no_activity(client,admin,db):
    account=db.scalar(select(Account).where(Account.role=="admin"))
    session=db.scalar(select(AuthSession).where(AuthSession.account_id==account.id))
    before=session.last_activity_at
    assert client.get("/api/v1/status").status_code==200
    db.refresh(session);assert session.last_activity_at==before
    with patch.object(sessions,"now_utc",return_value=before+timedelta(minutes=30)):
        assert client.get("/api/v1/status").status_code==401
    row=Account(username="status-tech",display_name="Tech",role="technician",password_hash=hash_password(PASSWORD))
    db.add(row);db.commit()
    assert client.post("/api/v1/auth/login",json={"username":row.username,"password":PASSWORD},headers=HEADERS).status_code==200
    assert client.get("/api/v1/status").status_code==403
    row.must_change_password=True;db.commit()
    assert client.get("/api/v1/status").status_code==403


def test_status_unauthenticated_denied_and_readiness_failure_safe(client,admin,monkeypatch,caplog):
    client.cookies.clear()
    assert client.get("/api/v1/status").status_code==401
    assert client.post("/api/v1/auth/login",json={"username":"admin","password":PASSWORD},headers=HEADERS).status_code==200
    from app.database.session import SessionLocal
    sentinel="database-secret-sentinel-do-not-display"
    with patch.object(SessionLocal.class_,"execute",side_effect=RuntimeError(sentinel)):
        for path in ("/health","/health/ready"):
            response=client.get(path)
            assert response.status_code==503 and sentinel not in response.text+caplog.text
        assert client.get("/health/live").status_code==200

import socket
import subprocess
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete
from app.config import get_settings
from app.database.session import SessionLocal
from app.database.models import (
    Account,
    AuthSession,
    CanonicalRecord,
    ChatMessage,
    ChatSession,
    Dataset,
    DatasetGrant,
    EmbeddingRecord,
    ExtractedImage,
    ImportJob,
    IncidentAnalysis,
    LoginRateBucket,
    ParseRun,
    Report,
    Source,
    SourceVersion,
)
from scripts.bootstrap_admin import bootstrap_admin

PASSWORD = "test-password-fifteen-plus"
HEADERS = {"Origin": "http://next-test:3000", "X-Requested-With": "RAG-Web", "Content-Type": "application/json"}


def reset_database():
    assert get_settings().test_mode, "Never reset operational DB"
    with SessionLocal.begin() as db:
        db.execute(Source.__table__.update().values(active_version_id=None))
        for model in (
            Report,
            ExtractedImage,
            IncidentAnalysis,
            EmbeddingRecord,
            ChatMessage,
            ChatSession,
            CanonicalRecord,
            ParseRun,
            ImportJob,
            SourceVersion,
            Source,
            DatasetGrant,
            AuthSession,
            LoginRateBucket,
            Dataset,
            Account,
        ):
            db.execute(delete(model))


@pytest.fixture(scope="session", autouse=True)
def migrate():
    if not get_settings().test_mode:
        pytest.skip("Integration tests require test_mode=True and isolated postgres-test/rag_test")
    subprocess.run(["python", "-m", "alembic", "upgrade", "head"], check=True)



@pytest.fixture(autouse=True)
def deny_outbound(monkeypatch):
    original = socket.getaddrinfo
    def allowed(host, *args, **kwargs):
        if host not in ("postgres-test", "localhost", "127.0.0.1", "::1", None):
            raise AssertionError("Outbound network denied in tests")
        return original(host, *args, **kwargs)
    monkeypatch.setattr(socket, "getaddrinfo", allowed)


@pytest.fixture
def db():
    reset_database()
    with SessionLocal() as session:
        yield session
        session.rollback()


@pytest.fixture
def client(db):
    from app.main import app
    with TestClient(app, base_url="http://next-test:3000") as value:
        yield value


@pytest.fixture
def admin(client):
    bootstrap_admin("admin", PASSWORD)
    response = client.post("/api/v1/auth/login", json={"username":"admin", "password":PASSWORD}, headers=HEADERS)
    assert response.status_code == 200, response.text
    return {**HEADERS, "X-CSRF-Token": response.json()["csrf_token"]}

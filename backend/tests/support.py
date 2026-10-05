"""Isolated E2E fixtures, mounted only when TEST_MODE validates rag_test."""
from fastapi import APIRouter
from sqlalchemy import select, func
from app.database.session import SessionLocal
from app.database.models import Account, AuthSession, Dataset
from tests.conftest import reset_database, PASSWORD
from scripts.bootstrap_admin import bootstrap_admin
from app.auth.sessions import digest

router=APIRouter(prefix="/api/v1/_test")

@router.post("/reset")
def reset():
    reset_database()
    bootstrap_admin("browser-admin",PASSWORD)
    with SessionLocal.begin() as db:
        db.add(Dataset(name="Browser WMS",description="Isolated browser evidence"))
    return {"username":"browser-admin","password":PASSWORD}

@router.post("/proof")
def proof(payload:dict):
    with SessionLocal() as db:
        row=db.scalar(select(AuthSession).where(AuthSession.token_digest==digest(payload["token"])))
        return {"session_exists":row is not None,"digest_only":row is not None and row.token_digest!=payload["token"],"dataset_exists":db.scalar(select(func.count()).select_from(Dataset).where(Dataset.name=="Browser WMS"))==1,"revoked":row is not None and row.revoked_at is not None}

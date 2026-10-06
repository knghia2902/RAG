"""Isolated E2E fixtures, mounted only when TEST_MODE validates rag_test."""
from datetime import datetime, timedelta, timezone
from typing import Literal
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, ConfigDict
from sqlalchemy import select, func
from app.database.session import SessionLocal
from app.database.models import Account, AuthSession, Dataset
from tests.conftest import reset_database, PASSWORD
from scripts.bootstrap_admin import bootstrap_admin
from app.auth.sessions import digest
from app.auth import sessions
from app.config import get_settings

_clock_now: datetime | None = None
def fixture_now():
    return _clock_now or datetime.now(timezone.utc)

router=APIRouter(prefix="/api/v1/_test")

@router.post("/reset")
def reset():
    global _clock_now
    _clock_now = None
    reset_database()
    bootstrap_admin("browser-admin",PASSWORD)
    with SessionLocal.begin() as db:
        db.add(Dataset(name="Browser WMS",description="Isolated browser evidence"))
    return {"username":"browser-admin","password":PASSWORD}


class ClockInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    offset_seconds: Literal[0] | None = None
    token: str | None = Field(default=None, min_length=1, max_length=128)
    cutoff: Literal["idle", "absolute"] | None = None


@router.post("/clock")
def clock(payload: ClockInput):
    """Isolated fixture-only clock, never alter host time or production settings."""
    global _clock_now
    assert get_settings().test_mode
    sessions.now_utc = fixture_now
    if payload.offset_seconds == 0 and payload.cutoff is None:
        _clock_now = None
        return {"controlled": False}
    if not payload.token or not payload.cutoff:
        raise HTTPException(422, "Token and cutoff required")
    with SessionLocal.begin() as db:
        row = db.scalar(select(AuthSession).where(AuthSession.token_digest == digest(payload.token)).with_for_update())
        if row is None:
            raise HTTPException(404, "Fixture session missing")
        if payload.cutoff == "idle":
            _clock_now = row.last_activity_at + timedelta(minutes=30)
        else:
            _clock_now = row.created_at + timedelta(hours=8)
            # Keep idle valid so the browser proves the absolute cutoff itself.
            row.last_activity_at = _clock_now - timedelta(minutes=1)
    return {"controlled": True}


class SessionTimeInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    token: str = Field(min_length=1, max_length=128)


@router.post("/session-time")
def session_time(payload: SessionTimeInput):
    assert get_settings().test_mode
    with SessionLocal() as db:
        row = db.scalar(select(AuthSession).where(AuthSession.token_digest == digest(payload.token)))
        if row is None:
            raise HTTPException(404, "Fixture session missing")
        return {"created_at": row.created_at.isoformat(), "last_activity_at": row.last_activity_at.isoformat()}

@router.post("/proof")
def proof(payload:dict):
    with SessionLocal() as db:
        row=db.scalar(select(AuthSession).where(AuthSession.token_digest==digest(payload["token"])))
        return {"session_exists":row is not None,"digest_only":row is not None and row.token_digest!=payload["token"],"dataset_exists":db.scalar(select(func.count()).select_from(Dataset).where(Dataset.name=="Browser WMS"))==1,"revoked":row is not None and row.revoked_at is not None}

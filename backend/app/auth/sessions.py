import hashlib
import secrets
from datetime import datetime, timezone
from sqlalchemy import select
from fastapi import HTTPException
from app.database.models import Account, AuthSession

SESSION_COOKIE = "rag_session"
CSRF_COOKIE = "rag_csrf"


def now_utc():
    return datetime.now(timezone.utc)


def digest(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def create_session(db, account, created_at=None):
    token, csrf = secrets.token_urlsafe(32), secrets.token_urlsafe(32)
    now = now_utc()
    row = AuthSession(account_id=account.id, token_digest=digest(token), csrf_digest=digest(csrf),
                      created_at=created_at or now, last_activity_at=now)
    db.add(row)
    db.flush()
    return row, token, csrf


def resolve_session(db, token: str | None, lock=False):
    if not token or len(token) > 128:
        raise HTTPException(401, "Phiên đăng nhập không hợp lệ")
    query = select(AuthSession).where(AuthSession.token_digest == digest(token))
    if lock:
        query = query.with_for_update()
    row = db.execute(query.execution_options(populate_existing=True)).scalar_one_or_none()
    if row is None or row.revoked_at is not None:
        raise HTTPException(401, "Phiên đăng nhập không hợp lệ")
    account = db.execute(select(Account).where(Account.id == row.account_id).execution_options(populate_existing=True)).scalar_one_or_none()
    if account is None or not account.active:
        raise HTTPException(401, "Phiên đăng nhập không hợp lệ")
    return row, account


def set_cookies(response, token, csrf):
    for name, value in ((SESSION_COOKIE, token), (CSRF_COOKIE, csrf)):
        response.set_cookie(name, value, httponly=True, secure=False, samesite="strict", path="/", max_age=8 * 3600)


def clear_cookies(response):
    for name in (SESSION_COOKIE, CSRF_COOKIE):
        response.delete_cookie(name, httponly=True, secure=False, samesite="strict", path="/")

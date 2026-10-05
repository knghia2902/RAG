from fastapi import Depends, HTTPException, Request
from app.database.session import get_db
from app.auth.sessions import SESSION_COOKIE, resolve_session
from app.auth.csrf import validate_csrf, validate_request


def get_identity(request: Request, db=Depends(get_db)):
    return resolve_session(db, request.cookies.get(SESSION_COOKIE))


def get_account(identity=Depends(get_identity)):
    account = identity[1]
    if account.must_change_password:
        raise HTTPException(403, "Phải đổi mật khẩu")
    return account


def unsafe_identity(request: Request, db=Depends(get_db)):
    validate_request(request)
    identity = resolve_session(db, request.cookies.get(SESSION_COOKIE), lock=True)
    validate_csrf(request, identity[0])
    return identity

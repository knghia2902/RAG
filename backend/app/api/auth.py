from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy import select
from app.database.session import get_db
from app.database.models import Account
from app.auth.passwords import dummy_hash, verify_password
from app.auth.sessions import CSRF_COOKIE, create_session, set_cookies, clear_cookies, digest, now_utc
from app.auth.csrf import validate_request
from app.api.dependencies import get_identity, unsafe_identity
from app.api.schemas import AccountDTO, LoginInput, SessionDTO

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.post("/login", response_model=SessionDTO)
def login(payload: LoginInput, request: Request, response: Response, db=Depends(get_db)):
    validate_request(request)
    account = db.execute(select(Account).where(Account.username == payload.username)).scalar_one_or_none()
    valid = verify_password(payload.password, account.password_hash if account else dummy_hash)
    if not valid or account is None or not account.active:
        raise HTTPException(401, "Tên đăng nhập hoặc mật khẩu không đúng")
    row, token, csrf = create_session(db, account)
    db.commit()
    set_cookies(response, token, csrf)
    return SessionDTO(account=AccountDTO.model_validate(account), csrf_token=csrf)


@router.get("/session", response_model=SessionDTO)
def inspect_session(request: Request, identity=Depends(get_identity)):
    row, account = identity
    csrf = request.cookies.get(CSRF_COOKIE, "")
    if digest(csrf) != row.csrf_digest:
        raise HTTPException(401, "Phiên đăng nhập không hợp lệ")
    return SessionDTO(account=AccountDTO.model_validate(account), csrf_token=csrf)


@router.post("/logout", status_code=204)
def logout(response: Response, identity=Depends(unsafe_identity), db=Depends(get_db)):
    identity[0].revoked_at = now_utc()
    db.commit()
    clear_cookies(response)

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy import select
from app.database.session import get_db
from app.database.models import Account
from app.auth.passwords import dummy_hash, verify_password
from app.auth.sessions import CSRF_COOKIE, create_session, set_cookies, clear_cookies, digest, now_utc, record_activity
from app.auth.csrf import validate_request
from app.api.dependencies import get_identity, unsafe_identity
from app.api.schemas import AccountDTO, LoginInput, SessionDTO
from app.auth import rate_limit

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.post("/login", response_model=SessionDTO)
def login(payload: LoginInput, request: Request, response: Response, db=Depends(get_db)):
    validate_request(request)
    source=request.client.host if request.client else "unknown"
    rate_limit.check_limit(db,payload.username,source)
    account = db.execute(select(Account).where(Account.username == payload.username).with_for_update()).scalar_one_or_none()
    valid = verify_password(payload.password, account.password_hash if account else dummy_hash)
    if not valid or account is None or not account.active:
        rate_limit.record_failure(db,payload.username,source)
        db.commit()
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


@router.post("/activity", status_code=204)
def activity(identity=Depends(unsafe_identity), db=Depends(get_db)):
    record_activity(db, identity[0])
    db.commit()


from pydantic import Field
from app.api.schemas import DTO
class PasswordChange(DTO):
    current_password: str=Field(min_length=8,max_length=128)
    new_password: str=Field(min_length=8,max_length=128)


def password_identity(request:Request,db=Depends(get_db)):
    from app.database.models import AdminGuard
    validate_request(request)
    db.execute(select(AdminGuard).where(AdminGuard.id==1).with_for_update()).scalar_one()
    return unsafe_identity(request,db)


@router.post("/change-password",response_model=SessionDTO)
def change_password(payload:PasswordChange,response:Response,identity=Depends(password_identity),db=Depends(get_db)):
    from app.auth.passwords import hash_password
    from app.auth.accounts import revoke_sessions
    row,account=identity
    if not verify_password(payload.current_password,account.password_hash):raise HTTPException(400,"Mật khẩu hiện tại không đúng")
    if payload.current_password==payload.new_password:raise HTTPException(422,"Mật khẩu mới phải khác mật khẩu hiện tại")
    account.password_hash=hash_password(payload.new_password);account.must_change_password=False
    original_created=row.created_at
    revoke_sessions(db,account.id)
    new,token,csrf=create_session(db,account,created_at=original_created)
    db.commit();set_cookies(response,token,csrf)
    return SessionDTO(account=AccountDTO.model_validate(account),csrf_token=csrf)

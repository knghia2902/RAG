from uuid import UUID
from fastapi import APIRouter, Depends, Request, Query
from sqlalchemy import select,func
from app.database.models import Account
from app.database.session import get_db
from app.auth import accounts
from app.auth.policy import require_admin
from app.auth.csrf import validate_request,validate_csrf
from app.auth.sessions import resolve_session,SESSION_COOKIE
from app.api.dependencies import get_account
from app.api.schemas import AccountCreate,AccountPatch,PasswordReset,AccountDTO,AccountPage

router=APIRouter(prefix="/api/v1/admin/users",tags=["accounts"])


def manager(account=Depends(get_account)):
    require_admin(account);return account


def mutation_manager(request:Request,db=Depends(get_db)):
    validate_request(request)
    # Guard first, then resolve current session; never hold an actor session row
    # while waiting for guard and revoking the other actor's sessions.
    from app.database.models import AdminGuard
    db.execute(select(AdminGuard).where(AdminGuard.id==1).with_for_update()).scalar_one()
    identity=resolve_session(db,request.cookies.get(SESSION_COOKIE))
    validate_csrf(request,identity[0])
    return manager(identity[1])


@router.get("",response_model=AccountPage)
def list_users(page:int=Query(1,ge=1),page_size:int=Query(25,ge=1,le=100),actor=Depends(manager),db=Depends(get_db)):
    total=db.scalar(select(func.count()).select_from(Account))
    rows=db.scalars(select(Account).order_by(Account.username).offset((page-1)*page_size).limit(page_size)).all()
    return AccountPage(items=[AccountDTO.model_validate(row) for row in rows],total=total,page=page,page_size=page_size)


@router.post("",response_model=AccountDTO,status_code=201)
def create(payload:AccountCreate,actor=Depends(mutation_manager),db=Depends(get_db)):
    row=accounts.create_account(db,actor,payload);db.commit();accounts.record_audit(actor,"account.create",row)
    return row


@router.patch("/{target_id}",response_model=AccountDTO)
def update(target_id:UUID,payload:AccountPatch,actor=Depends(mutation_manager),db=Depends(get_db)):
    row=accounts.update_account(db,actor,target_id,payload);db.commit();accounts.record_audit(actor,"account.update",row)
    return row


@router.post("/{target_id}/reset-password",response_model=AccountDTO)
def reset(target_id:UUID,payload:PasswordReset,actor=Depends(mutation_manager),db=Depends(get_db)):
    row=accounts.reset_password(db,actor,target_id,payload);db.commit();accounts.record_audit(actor,"account.reset_password",row)
    return row

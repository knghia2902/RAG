import logging
from fastapi import HTTPException
from sqlalchemy import select, func, update
from sqlalchemy.exc import IntegrityError
from app.database.models import Account, AdminGuard, AuthSession
from app.auth.passwords import hash_password
from app.auth.sessions import now_utc

audit=logging.getLogger("rag.audit")


def lock_manager(db, actor):
    db.execute(select(AdminGuard).where(AdminGuard.id==1).with_for_update()).scalar_one()
    current=db.execute(select(Account).where(Account.id==actor.id).execution_options(populate_existing=True)).scalar_one()
    if not current.active or current.role!="admin":
        raise HTTPException(403,"Không đủ quyền")
    if current.must_change_password:
        raise HTTPException(403,"password_change_required")
    return current


def revoke_sessions(db,account_id):
    db.execute(update(AuthSession).where(AuthSession.account_id==account_id,AuthSession.revoked_at.is_(None)).values(revoked_at=now_utc()))


def create_account(db,actor,payload):
    lock_manager(db,actor)
    row=Account(username=payload.username,display_name=payload.display_name,role=payload.role,
                password_hash=hash_password(payload.temporary_password),must_change_password=True)
    db.add(row)
    try:db.flush()
    except IntegrityError:
        db.rollback();raise HTTPException(409,"Tên đăng nhập đã tồn tại")
    return row


def update_account(db,actor,target_id,payload):
    lock_manager(db,actor)
    row=db.execute(select(Account).where(Account.id==target_id).with_for_update()).scalar_one_or_none()
    if row is None:raise HTTPException(404,"Không tìm thấy tài khoản")
    values=payload.model_dump(exclude_unset=True)
    if any(value is None for value in values.values()):raise HTTPException(422,"Dữ liệu không hợp lệ")
    role=values.get("role",row.role);active=values.get("active",row.active)
    removes_admin=row.role=="admin" and row.active and (role!="admin" or not active)
    if removes_admin:
        count=db.scalar(select(func.count()).select_from(Account).where(Account.role=="admin",Account.active.is_(True)))
        if row.id==actor.id or count<=1:raise HTTPException(409,"Không thể vô hiệu hóa hoặc hạ quyền Admin hiện tại/cuối cùng")
    revoke=role!=row.role or (row.active and not active)
    for field,value in values.items():setattr(row,field,value)
    if revoke:revoke_sessions(db,row.id)
    db.flush()
    return row


def reset_password(db,actor,target_id,payload):
    lock_manager(db,actor)
    row=db.execute(select(Account).where(Account.id==target_id).with_for_update()).scalar_one_or_none()
    if row is None:raise HTTPException(404,"Không tìm thấy tài khoản")
    row.password_hash=hash_password(payload.temporary_password);row.must_change_password=True
    revoke_sessions(db,row.id);db.flush()
    return row


def record_audit(actor,action,target):
    audit.warning("actor=%s action=%s object=%s",actor.id,action,target.id)

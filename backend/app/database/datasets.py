from fastapi import HTTPException
import logging
from sqlalchemy import func, select, delete
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import IntegrityError
from app.database.models import Account, Dataset, DatasetGrant
from app.auth.policy import current_account, dataset_query, allowed_dataset_ids, require_admin
from app.api.schemas import DatasetDTO, DatasetPage

logger = logging.getLogger("rag.audit")


def technician_target(db, target_id):
    row = db.scalar(select(Account).where(Account.id==target_id, Account.role=="technician"))
    if row is None:
        raise HTTPException(404, "Không tìm thấy Kỹ thuật viên")
    return row


def grants(db, actor, target_id):
    require_admin(current_account(db, actor))
    technician_target(db, target_id)
    return {"dataset_ids": list(db.scalars(select(DatasetGrant.dataset_id).where(DatasetGrant.account_id==target_id).order_by(DatasetGrant.dataset_id)))}


def set_grant(db, actor, target_id, dataset_id, present):
    # The API's shared administration guard serializes this commit with role
    # changes and opposing grant writes; each request mutates only one pair.
    require_admin(current_account(db, actor))
    technician_target(db, target_id)
    if db.get(Dataset, dataset_id) is None:
        raise HTTPException(404, "Không tìm thấy Dataset")
    if present:
        db.execute(insert(DatasetGrant).values(account_id=target_id, dataset_id=dataset_id).on_conflict_do_nothing(index_elements=[DatasetGrant.account_id, DatasetGrant.dataset_id]))
    else:
        db.execute(delete(DatasetGrant).where(DatasetGrant.account_id==target_id, DatasetGrant.dataset_id==dataset_id))
    result = grants(db, actor, target_id)
    db.commit()
    logger.warning("actor=%s action=%s account=%s dataset=%s", actor.id, "dataset.grant" if present else "dataset.revoke", target_id, dataset_id)
    return result


def recheck_response(db, account, initial_scope, detail=False):
    # READ COMMITTED + fresh SQL, never the session identity-map snapshot.
    current_scope = allowed_dataset_ids(db, account)
    if not initial_scope.issubset(current_scope):
        raise HTTPException(404 if detail else 403, "Không tìm thấy Dataset" if detail else "Quyền truy cập đã thay đổi")


def list_metadata(db, account, page, page_size):
    account = current_account(db, account)
    scope = allowed_dataset_ids(db, account)
    query = dataset_query(account).where(Dataset.id.in_(scope))
    total = db.scalar(select(func.count()).select_from(query.subquery()))
    rows = db.scalars(query.order_by(Dataset.created_at, Dataset.id).offset((page-1)*page_size).limit(page_size)).all()
    result = DatasetPage(items=[DatasetDTO.model_validate(row) for row in rows], total=total, page=page, page_size=page_size)
    recheck_response(db, account, scope)
    return result


def detail_metadata(db, account, dataset_id):
    account = current_account(db, account)
    row = db.scalar(dataset_query(account).where(Dataset.id==dataset_id))
    if row is None:
        raise HTTPException(404, "Không tìm thấy Dataset")
    result = DatasetDTO.model_validate(row)
    recheck_response(db, account, {row.id}, detail=True)
    return result


def save_metadata(db, account, payload, dataset_id=None):
    require_admin(current_account(db, account))
    row = db.get(Dataset, dataset_id) if dataset_id else Dataset()
    if row is None:
        raise HTTPException(404, "Không tìm thấy Dataset")
    for name, value in payload.model_dump(exclude_unset=True).items():
        setattr(row, name, value)
    db.add(row)
    try:
        db.flush(); db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Tên Dataset đã tồn tại")
    return DatasetDTO.model_validate(row)

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from app.database.models import Dataset
from app.auth.policy import current_account, dataset_query, allowed_dataset_ids, require_admin
from app.api.schemas import DatasetDTO, DatasetPage


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

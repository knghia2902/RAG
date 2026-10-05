from sqlalchemy import select
from fastapi import HTTPException
from app.database.models import Dataset, DatasetGrant


def require_admin(account):
    if account.role != "admin":
        raise HTTPException(403, "Không đủ quyền")


def dataset_query(account):
    query = select(Dataset)
    if account.role == "admin":
        return query
    if account.role != "technician":
        raise HTTPException(403, "Không đủ quyền")
    return query.where(Dataset.id.in_(select(DatasetGrant.dataset_id).where(DatasetGrant.account_id == account.id)))

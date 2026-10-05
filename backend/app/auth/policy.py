from sqlalchemy import select
from fastapi import HTTPException
from app.database.models import Account, Dataset, DatasetGrant

CAPABILITIES = {
    "admin": {"accounts.manage", "datasets.manage", "repository.upload", "repository.delete", "repository.reindex", "metadata.read", "analyze", "ticket.analyze", "report.create", "report.read"},
    "technician": {"metadata.read", "analyze", "ticket.analyze", "report.create", "report.read"},
}


def current_account(db, account):
    row = db.scalar(select(Account).where(Account.id == account.id).execution_options(populate_existing=True))
    if row is None or not row.active:
        raise HTTPException(401, "Phiên đăng nhập không hợp lệ")
    if row.must_change_password:
        raise HTTPException(403, "password_change_required")
    return row


def has_capability(account, capability):
    return account.active and not account.must_change_password and capability in CAPABILITIES.get(account.role, set())


def allowed_dataset_ids(db, account):
    account = current_account(db, account)
    if not has_capability(account, "metadata.read"):
        raise HTTPException(403, "Không đủ quyền")
    return set(db.scalars(dataset_query(account).with_only_columns(Dataset.id)).all())


def require_all_datasets(db, account, dataset_ids, capability="metadata.read"):
    account = current_account(db, account)
    ids = set(dataset_ids)
    if not has_capability(account, capability) or not ids or not ids.issubset(allowed_dataset_ids(db, account)):
        raise HTTPException(403, "Quyền truy cập đã thay đổi")


def require_admin(account):
    if not has_capability(account, "datasets.manage"):
        raise HTTPException(403, "Không đủ quyền")


def dataset_query(account):
    query = select(Dataset)
    if account.role == "admin":
        return query
    if account.role != "technician":
        raise HTTPException(403, "Không đủ quyền")
    return query.where(Dataset.id.in_(select(DatasetGrant.dataset_id).where(DatasetGrant.account_id == account.id)))

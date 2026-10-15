from sqlalchemy import select
from fastapi import HTTPException
from app.database.models import Account, Dataset, DatasetGrant
from dataclasses import dataclass
from uuid import UUID

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


@dataclass(frozen=True)
class Principal:
    """Backend-only snapshot; callers must reload it before each resource response."""
    role: str
    dataset_ids: frozenset[UUID]
    active: bool = True
    must_change_password: bool = False


def current_principal(db, account):
    account = current_account(db, account)
    grants = frozenset(db.scalars(select(DatasetGrant.dataset_id).where(DatasetGrant.account_id == account.id)))
    return Principal(account.role, grants, account.active, account.must_change_password)


def require_all_datasets(principal, provenance_ids, capability="metadata.read", *, capability_mapping=None):
    """Pure, whole-resource decision; never return a partially authorized resource."""
    mapping = CAPABILITIES if capability_mapping is None else capability_mapping
    permitted = principal.active and not principal.must_change_password and capability in mapping.get(principal.role, set())
    if not permitted:
        raise HTTPException(403, "permission_changed")
    # Admin report access is global, including legacy resources without provenance.
    if principal.role == "admin":
        return
    ids = frozenset(provenance_ids or ())
    if not ids or not ids.issubset(principal.dataset_ids):
        raise HTTPException(403, "permission_changed")


def authorize_resource(db, account, provenance_ids, capability="metadata.read"):
    """Shared service seam: current SQL identity/grants before pure authorization."""
    require_all_datasets(current_principal(db, account), provenance_ids, capability)


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


def verify_dataset_access(account, dataset_id, db):
    account = current_account(db, account)
    scope = allowed_dataset_ids(db, account)
    if dataset_id not in scope:
        raise HTTPException(403, "Tài khoản không có quyền truy cập dataset này.")
    return account


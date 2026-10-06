from uuid import uuid4
import pytest
from fastapi import HTTPException
from app.auth import policy


def principal(role="technician", grants=(), active=True, must_change_password=False):
    assert hasattr(policy, "Principal"), "Current authorization snapshot contract is missing"
    return policy.Principal(role=role, dataset_ids=frozenset(grants), active=active,
                            must_change_password=must_change_password)


def test_composite_resource_denied_entirely_after_revocation():
    a, b = uuid4(), uuid4()
    policy.require_all_datasets(principal(grants=(a,b)), (a,b), capability="report.read")
    with pytest.raises(HTTPException) as exc:
        policy.require_all_datasets(principal(grants=(b,)), (a,b), capability="report.read")
    assert exc.value.status_code == 403
    assert exc.value.detail == "permission_changed"
    assert str(a) not in str(exc.value.detail) and str(b) not in str(exc.value.detail)
    policy.require_all_datasets(principal(grants=(b,)), (b,), capability="report.read")


@pytest.mark.parametrize("ids", [(), None])
def test_technician_missing_provenance_denied(ids):
    with pytest.raises(HTTPException):
        policy.require_all_datasets(principal(), ids, capability="report.read")


def test_current_active_admin_has_global_report_read():
    policy.require_all_datasets(principal("admin"), (uuid4(),), capability="report.read")
    policy.require_all_datasets(principal("admin"), (), capability="report.read")


@pytest.mark.parametrize("kwargs", [{"active":False}, {"role":"admin","active":False}, {"must_change_password":True}, {"role":"admin","must_change_password":True}, {"role":"unknown"}])
def test_inactive_password_change_or_unknown_role_denied(kwargs):
    with pytest.raises(HTTPException):
        policy.require_all_datasets(principal(**kwargs), (uuid4(),), capability="report.read")


def test_role_capability_extension_needs_no_rag_changes():
    dataset = uuid4()
    reviewer = principal("reviewer", (dataset,))
    with pytest.raises(HTTPException):
        policy.require_all_datasets(reviewer, (dataset,), capability="report.read")
    policy.require_all_datasets(reviewer, (dataset,), capability="report.read",
                                capability_mapping={"reviewer": {"report.read"}})
    with pytest.raises(HTTPException):
        policy.require_all_datasets(reviewer, (uuid4(),), capability="report.read",
                                    capability_mapping={"reviewer": {"report.read"}})


def test_ticket_analysis_does_not_grant_repository_management():
    tech = principal()
    assert policy.has_capability(tech, "ticket.analyze")
    for action in ("repository.upload", "repository.delete", "repository.reindex"):
        assert not policy.has_capability(tech, action)


def test_resource_service_reloads_current_database_state(db):
    from sqlalchemy import delete, update
    from app.database.models import Account, Dataset, DatasetGrant
    from app.database.session import SessionLocal
    from app.auth.passwords import hash_password
    from tests.conftest import PASSWORD
    account = Account(username="policy-tech", display_name="Tech",role="technician",password_hash=hash_password(PASSWORD))
    a,b = Dataset(name="Policy A"), Dataset(name="Policy B")
    db.add_all([account,a,b]);db.flush()
    db.add_all([DatasetGrant(account_id=account.id,dataset_id=row.id) for row in (a,b)]);db.commit()
    policy.authorize_resource(db,account,(a.id,b.id),capability="report.read")
    with SessionLocal.begin() as other:
        other.execute(delete(DatasetGrant).where(DatasetGrant.account_id==account.id,DatasetGrant.dataset_id==a.id))
    with pytest.raises(HTTPException) as exc:
        policy.authorize_resource(db,account,(a.id,b.id),capability="report.read")
    assert exc.value.detail=="permission_changed"
    policy.authorize_resource(db,account,(b.id,),capability="report.read")
    with SessionLocal.begin() as other:
        other.execute(update(Account).where(Account.id==account.id).values(active=False))
    with pytest.raises(HTTPException):
        policy.authorize_resource(db,account,(b.id,),capability="report.read")

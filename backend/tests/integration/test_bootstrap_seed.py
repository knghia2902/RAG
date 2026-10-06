import importlib
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from unittest.mock import patch
import pytest
from sqlalchemy import select, delete
from app.database.models import Account, Dataset, DatasetGrant
from app.database.session import SessionLocal
from scripts.bootstrap_admin import bootstrap_admin
from tests.conftest import PASSWORD


def seed_module():
    assert importlib.util.find_spec("scripts.seed_demo"), "Separate replay-safe demo seed is missing"
    return importlib.import_module("scripts.seed_demo")


def snapshot():
    with SessionLocal() as db:
        return (
            [(a.id,a.username,a.display_name,a.password_hash,a.role,a.active,a.must_change_password) for a in db.scalars(select(Account).order_by(Account.username))],
            [(d.id,d.name,d.description) for d in db.scalars(select(Dataset).order_by(Dataset.name))],
            [(g.account_id,g.dataset_id) for g in db.scalars(select(DatasetGrant).order_by(DatasetGrant.account_id,DatasetGrant.dataset_id))],
        )


def test_seed_requires_bootstrap_and_does_not_become_user_factory(db):
    seed=seed_module()
    with pytest.raises(ValueError): seed.seed_demo(PASSWORD,PASSWORD)
    assert snapshot()==([],[],[])
    bootstrap_admin("admin",PASSWORD)
    seed.seed_demo(PASSWORD,PASSWORD)
    accounts,datasets,grants=snapshot()
    assert len(accounts)==3 and len(datasets)==1 and len(grants)==1
    assert {a[4] for a in accounts}=={"admin","technician"}
    for name in ("demo-granted","demo-ungranted"):
        account=next(a for a in accounts if a[1]==name)
        assert account[3]!=PASSWORD and account[6]
    assert not bootstrap_admin("replacement",PASSWORD)
    assert snapshot()[0]==accounts


def test_seed_replay_preserves_password_role_active_metadata_and_revoked_grant(db):
    seed=seed_module();bootstrap_admin("admin",PASSWORD);seed.seed_demo(PASSWORD,PASSWORD)
    with SessionLocal.begin() as other:
        granted=other.scalar(select(Account).where(Account.username=="demo-granted"))
        granted.display_name="Operator edit";granted.active=False;granted.role="admin"
        dataset=other.scalar(select(Dataset));dataset.description="Operator metadata"
        other.execute(delete(DatasetGrant))
    before=snapshot()
    seed.seed_demo("different-valid-password", "another-valid-password")
    assert snapshot()==before


def test_concurrent_seed_services_have_one_complete_initial_grant(db):
    seed=seed_module();bootstrap_admin("admin",PASSWORD);barrier=Barrier(2)
    def run(_):
        barrier.wait(timeout=10)
        return seed.seed_demo(PASSWORD,PASSWORD)
    with ThreadPoolExecutor(max_workers=2) as pool:
        results=list(pool.map(run,range(2)))
    assert sorted(results)==[False,True]
    accounts,datasets,grants=snapshot()
    assert len(accounts)==3 and len(datasets)==1 and len(grants)==1
    granted=next(a for a in accounts if a[1]=="demo-granted")
    assert grants==[(granted[0],datasets[0][0])]


def test_seed_crash_before_commit_rolls_back_entire_seed(db):
    seed=seed_module();bootstrap_admin("admin",PASSWORD);before=snapshot()
    original=SessionLocal.class_.flush
    def fail_grant(session,*args,**kwargs):
        if any(isinstance(row,DatasetGrant) for row in session.new):
            raise RuntimeError("Injected seed crash")
        return original(session,*args,**kwargs)
    with patch.object(SessionLocal.class_,"flush",fail_grant):
        with pytest.raises(RuntimeError): seed.seed_demo(PASSWORD,PASSWORD)
    assert snapshot()==before
    seed.seed_demo(PASSWORD,PASSWORD)
    assert len(snapshot()[2])==1


def test_seed_cli_getpass_separate_from_bootstrap(monkeypatch,db,capsys):
    seed=seed_module();bootstrap_admin("admin",PASSWORD)
    monkeypatch.setattr(seed.getpass,"getpass",lambda _:PASSWORD)
    seed.main()
    output=capsys.readouterr().out
    assert PASSWORD not in output and "Admin" not in output
    before=snapshot();seed.main();assert snapshot()==before


def test_seed_does_not_grant_preexisting_technician(db):
    seed=seed_module();bootstrap_admin("admin",PASSWORD)
    from app.auth.passwords import hash_password
    row=Account(username="demo-granted",display_name="Existing",role="technician",password_hash=hash_password(PASSWORD))
    db.add(row);db.commit();before_hash=row.password_hash
    seed.seed_demo(PASSWORD,PASSWORD)
    db.refresh(row)
    assert row.password_hash==before_hash and row.display_name=="Existing"
    assert not snapshot()[2]


def test_concurrent_replay_never_restores_revoked_grant(db):
    seed=seed_module();bootstrap_admin("admin",PASSWORD);seed.seed_demo(PASSWORD,PASSWORD)
    with SessionLocal.begin() as other: other.execute(delete(DatasetGrant))
    before=snapshot()
    with ThreadPoolExecutor(max_workers=2) as pool:
        assert list(pool.map(lambda _:seed.seed_demo(PASSWORD,PASSWORD),range(2)))==[False,False]
    assert snapshot()==before


@pytest.mark.parametrize("password", ["short", "x"*129])
def test_invalid_seed_password_writes_nothing(db,password):
    seed=seed_module();bootstrap_admin("admin",PASSWORD);before=snapshot()
    with pytest.raises(ValueError):seed.seed_demo(password,PASSWORD)
    assert snapshot()==before

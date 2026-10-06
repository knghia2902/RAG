import subprocess
from concurrent.futures import ThreadPoolExecutor
import pytest
from sqlalchemy import text, select, func
from sqlalchemy.exc import IntegrityError, DBAPIError
from app.database.session import engine, SessionLocal
from app.database.models import Account
from scripts.bootstrap_admin import bootstrap_admin
from tests.conftest import PASSWORD


def test_head_vector_constraints_and_replay(db):
    bootstrap_admin("admin",PASSWORD)
    with engine.connect() as connection:
        assert connection.scalar(text("SELECT version_num FROM alembic_version"))=="0001_access_control"
        assert connection.scalar(text("SELECT extversion FROM pg_extension WHERE extname='vector'"))=="0.8.7"
        names=connection.scalars(text("SELECT conname FROM pg_constraint WHERE conrelid='accounts'::regclass")).all()
        assert "account_role" in names and "username_normalized" in names
    for _ in range(2):
        subprocess.run(["python","-m","alembic","upgrade","head"],check=True)
    assert db.scalar(select(func.count()).select_from(Account))==1
    with pytest.raises(DBAPIError):
        db.execute(text("UPDATE accounts SET username='changed'"));db.commit()
    db.rollback()


def test_empty_upgrade_and_not_ready_before_head(client,db):
    subprocess.run(["python","-m","alembic","downgrade","base"],check=True)
    assert client.get("/health/ready").status_code==503
    subprocess.run(["python","-m","alembic","upgrade","head"],check=True)
    assert client.get("/health/ready").status_code==200


def test_concurrent_bootstrap_at_most_one_admin(db):
    with ThreadPoolExecutor(max_workers=2) as pool:
        results=list(pool.map(lambda name:bootstrap_admin(name,PASSWORD),["admin-one","admin-two"]))
    assert sorted(results)==[False,True]
    assert db.scalar(select(func.count()).select_from(Account).where(Account.role=="admin"))==1


def test_independent_bootstrap_processes_serialize(db):
    code = "import sys; from scripts.bootstrap_admin import bootstrap_admin; " \
           "print(bootstrap_admin(sys.argv[1], 'test-password-fifteen-plus'))"
    processes = [subprocess.Popen(["python", "-c", code, name], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                 for name in ("process-one", "process-two")]
    results = []
    for process in processes:
        out, error = process.communicate(timeout=20)
        assert process.returncode == 0, error
        results.append(out.strip())
    assert sorted(results) == ["False", "True"]
    assert db.scalar(select(func.count()).select_from(Account)) == 1

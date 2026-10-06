"""Separate insert-only demo metadata/accounts command, never a bootstrap factory."""
import getpass
from sqlalchemy import select
from app.auth.passwords import hash_password
from app.database.models import Account, AdminGuard, Dataset, DatasetGrant
from app.database.session import SessionLocal


def seed_demo(granted_password: str, ungranted_password: str) -> bool:
    hashes = {"demo-granted": hash_password(granted_password),
              "demo-ungranted": hash_password(ungranted_password)}
    with SessionLocal.begin() as db:
        # Same guard as bootstrap/role/grant changes; all unique lookups and
        # initial grants remain in one transaction, including concurrent CLI runs.
        db.execute(select(AdminGuard).where(AdminGuard.id == 1).with_for_update()).scalar_one()
        if not db.scalar(select(Account.id).where(Account.role == "admin", Account.active.is_(True)).limit(1)):
            raise ValueError("Bootstrap an active Admin before demo seed")
        changed = False
        dataset = db.scalar(select(Dataset).where(Dataset.name == "Demo WMS"))
        if dataset is None:
            dataset = Dataset(name="Demo WMS", description="Dataset metadata demo; chưa có tài liệu")
            db.add(dataset); db.flush(); changed = True
        for username, display_name in (("demo-granted", "Kỹ thuật viên demo có quyền"),
                                       ("demo-ungranted", "Kỹ thuật viên demo chưa có quyền")):
            if db.scalar(select(Account.id).where(Account.username == username)):
                continue
            account = Account(username=username, display_name=display_name, role="technician",
                              password_hash=hashes[username], must_change_password=True)
            db.add(account); db.flush(); changed = True
            # Existing accounts are never edited or granted, even after revoke.
            if username == "demo-granted":
                db.add(DatasetGrant(account_id=account.id, dataset_id=dataset.id))
        db.flush()
    return changed


def main():
    values = []
    for username in ("demo-granted", "demo-ungranted"):
        password = getpass.getpass(f"Mật khẩu {username} (8–128 ký tự): ")
        if password != getpass.getpass("Nhập lại mật khẩu: "):
            raise SystemExit("Mật khẩu không khớp; không thay đổi dữ liệu")
        values.append(password)
    try:
        changed = seed_demo(*values)
    except ValueError:
        raise SystemExit("Cần bootstrap Admin và mật khẩu hợp lệ; không thay đổi dữ liệu")
    print("Đã thêm dữ liệu demo" if changed else "Đã có dữ liệu demo; không thay đổi")


if __name__ == "__main__":
    main()

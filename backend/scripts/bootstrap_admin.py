import getpass
from sqlalchemy import select
from app.auth.passwords import normalize_username, hash_password
from app.database.models import Account, AdminGuard
from app.database.session import SessionLocal


def bootstrap_admin(username: str, password: str, display_name: str | None = None):
    username = normalize_username(username)
    password_hash = hash_password(password)
    with SessionLocal.begin() as db:
        db.execute(select(AdminGuard).where(AdminGuard.id == 1).with_for_update()).scalar_one()
        if db.scalar(select(Account.id).where(Account.role == "admin").limit(1)):
            return False
        if db.scalar(select(Account.id).where(Account.username == username)):
            raise ValueError("Username already exists")
        db.add(Account(username=username, display_name=display_name or username, password_hash=password_hash, role="admin"))
    return True


def main():
    username = input("Username Admin: ")
    password = getpass.getpass("Mật khẩu (15–128 ký tự): ")
    if password != getpass.getpass("Nhập lại mật khẩu: "):
        raise SystemExit("Mật khẩu không khớp")
    try:
        created = bootstrap_admin(username, password)
    except ValueError:
        raise SystemExit("Dữ liệu không hợp lệ; không thay đổi tài khoản")
    print("Đã tạo Admin" if created else "Đã có Admin; không thay đổi tài khoản")


if __name__ == "__main__":
    main()

import re
from pwdlib import PasswordHash

password_hasher = PasswordHash.recommended()
dummy_hash = password_hasher.hash("dummy-password-for-timing-only")


def normalize_username(value: str) -> str:
    value = value.lower()
    if not re.fullmatch(r"[a-z0-9._-]{3,64}", value, flags=re.ASCII):
        raise ValueError("Username must contain 3–64 ASCII letters, digits, . _ -")
    return value


def validate_password(value: str) -> str:
    if not 15 <= len(value) <= 128:
        raise ValueError("Password must contain 15–128 characters")
    return value


def hash_password(value: str) -> str:
    return password_hasher.hash(validate_password(value))


def verify_password(value: str, encoded: str) -> bool:
    return password_hasher.verify(value, encoded)

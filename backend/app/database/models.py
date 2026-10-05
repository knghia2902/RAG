import uuid
from datetime import datetime, timezone
from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def utcnow():
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class Account(Base):
    __tablename__ = "accounts"
    __table_args__ = (CheckConstraint("role IN ('admin','technician')", name="account_role"),
                      CheckConstraint("username ~ '^[a-z0-9._-]{3,64}$'", name="username_normalized"),)
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    display_name: Mapped[str] = mapped_column(String(128), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(512), nullable=False)
    role: Mapped[str] = mapped_column(String(32), nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    must_change_password: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)


class AuthSession(Base):
    __tablename__ = "sessions"
    __table_args__ = (CheckConstraint("length(token_digest)=64 AND length(csrf_digest)=64", name="session_digests"),)
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("accounts.id"), index=True, nullable=False)
    token_digest: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    csrf_digest: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    last_activity_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Dataset(Base):
    __tablename__ = "datasets"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    description: Mapped[str] = mapped_column(String(2000), default="", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)


class DatasetGrant(Base):
    __tablename__ = "dataset_grants"
    account_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("accounts.id"), primary_key=True)
    dataset_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("datasets.id"), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)


class AdminGuard(Base):
    __tablename__ = "admin_guard"
    __table_args__ = (CheckConstraint("id = 1", name="singleton_guard"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True)


class LoginRateBucket(Base):
    __tablename__ = "login_rate_buckets"
    __table_args__ = (CheckConstraint("failures >= 0 AND failures <= 100", name="bounded_failures"),)
    key: Mapped[str] = mapped_column(String(64), primary_key=True)
    window_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    failures: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

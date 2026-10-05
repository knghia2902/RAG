"""Local identity and dataset access schema."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg

revision = "0001_access_control"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.create_table("accounts",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True),
        sa.Column("username", sa.String(64), nullable=False, unique=True),
        sa.Column("display_name", sa.String(128), nullable=False),
        sa.Column("password_hash", sa.String(512), nullable=False),
        sa.Column("role", sa.String(32), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.Column("must_change_password", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("role IN ('admin','technician')", name="account_role"),
        sa.CheckConstraint("username ~ '^[a-z0-9._-]{3,64}$'", name="username_normalized"))
    op.create_table("sessions",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True),
        sa.Column("account_id", pg.UUID(as_uuid=True), sa.ForeignKey("accounts.id"), nullable=False),
        sa.Column("token_digest", sa.String(64), nullable=False, unique=True),
        sa.Column("csrf_digest", sa.String(64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_activity_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True)),
        sa.CheckConstraint("length(token_digest)=64 AND length(csrf_digest)=64", name="session_digests"))
    op.create_index("ix_sessions_account_id", "sessions", ["account_id"])
    op.create_table("datasets", sa.Column("id", pg.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(128), nullable=False, unique=True),
        sa.Column("description", sa.String(2000), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False))
    op.create_table("dataset_grants",
        sa.Column("account_id", pg.UUID(as_uuid=True), sa.ForeignKey("accounts.id"), primary_key=True),
        sa.Column("dataset_id", pg.UUID(as_uuid=True), sa.ForeignKey("datasets.id"), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False))
    op.create_table("admin_guard", sa.Column("id", sa.Integer(), primary_key=True), sa.CheckConstraint("id = 1", name="singleton_guard"))
    op.execute("INSERT INTO admin_guard(id) VALUES (1)")
    op.create_table("login_rate_buckets", sa.Column("key", sa.String(64), primary_key=True),
        sa.Column("window_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("failures", sa.Integer(), nullable=False), sa.CheckConstraint("failures >= 0 AND failures <= 100", name="bounded_failures"))
    op.execute("""CREATE FUNCTION immutable_username() RETURNS trigger LANGUAGE plpgsql AS $$
        BEGIN IF NEW.username <> OLD.username THEN RAISE EXCEPTION 'username is immutable'; END IF; RETURN NEW; END $$""")
    op.execute("CREATE TRIGGER accounts_immutable_username BEFORE UPDATE ON accounts FOR EACH ROW EXECUTE FUNCTION immutable_username()")


def downgrade():
    op.execute("DROP TRIGGER accounts_immutable_username ON accounts")
    op.execute("DROP FUNCTION immutable_username()")
    for table in ("login_rate_buckets", "admin_guard", "dataset_grants", "datasets", "sessions", "accounts"):
        op.drop_table(table)

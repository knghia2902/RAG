"""Incident reports persistence schema."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg

revision = "0005_incident_reports"
down_revision = "0004_incident_analysis"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "reports",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "account_id",
            pg.UUID(as_uuid=True),
            sa.ForeignKey("accounts.id"),
            nullable=False,
        ),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("period_type", sa.String(32), nullable=False),
        sa.Column("start_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("dataset_ids", pg.JSONB, nullable=False),
        sa.Column("metrics_json", pg.JSONB, nullable=False),
        sa.Column("narrative_json", pg.JSONB, nullable=False),
        sa.Column("provenance_json", pg.JSONB, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_reports_account_id", "reports", ["account_id"])
    op.create_index("ix_reports_created_at", "reports", ["created_at"])


def downgrade():
    op.drop_table("reports")

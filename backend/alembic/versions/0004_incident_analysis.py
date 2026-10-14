"""Incident analysis persistence schema."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg

revision = "0004_incident_analysis"
down_revision = "0003_pgvector_and_chat"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "incident_analyses",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "account_id",
            pg.UUID(as_uuid=True),
            sa.ForeignKey("accounts.id"),
            nullable=False,
        ),
        sa.Column("order_id", sa.String(64), nullable=False),
        sa.Column("ticket_id", sa.String(64), nullable=True),
        sa.Column("input_mode", sa.String(32), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("classification_json", pg.JSONB, nullable=False),
        sa.Column("timeline_json", pg.JSONB, nullable=False),
        sa.Column("analysis_json", pg.JSONB, nullable=False),
        sa.Column("citations_json", pg.JSONB, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_incident_analyses_account_id", "incident_analyses", ["account_id"])
    op.create_index("ix_incident_analyses_order_id", "incident_analyses", ["order_id"])
    op.create_index("ix_incident_analyses_ticket_id", "incident_analyses", ["ticket_id"])


def downgrade():
    op.drop_table("incident_analyses")

"""Pgvector extension, embedding_records, and chat persistence schema."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg
from pgvector.sqlalchemy import Vector

revision = "0003_pgvector_and_chat"
down_revision = "0002_source_lifecycle"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("CREATE EXTENSION IF NOT EXISTS vector;")

    op.create_table(
        "embedding_records",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "canonical_record_id",
            pg.UUID(as_uuid=True),
            sa.ForeignKey("canonical_records.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "dataset_id",
            pg.UUID(as_uuid=True),
            sa.ForeignKey("datasets.id"),
            nullable=False,
        ),
        sa.Column(
            "source_version_id",
            pg.UUID(as_uuid=True),
            sa.ForeignKey("source_versions.id"),
            nullable=False,
        ),
        sa.Column("model_name", sa.String(128), nullable=False),
        sa.Column("dimension", sa.Integer(), nullable=False),
        sa.Column("index_version", pg.UUID(as_uuid=True), nullable=False),
        sa.Column("embedding", Vector(1536), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_embedding_records_canonical_record_id", "embedding_records", ["canonical_record_id"])
    op.create_index("ix_embedding_records_dataset_id", "embedding_records", ["dataset_id"])
    op.create_index("ix_embedding_records_source_version_id", "embedding_records", ["source_version_id"])

    op.create_table(
        "chat_sessions",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "account_id",
            pg.UUID(as_uuid=True),
            sa.ForeignKey("accounts.id"),
            nullable=False,
        ),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_chat_sessions_account_id", "chat_sessions", ["account_id"])

    op.create_table(
        "chat_messages",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "session_id",
            pg.UUID(as_uuid=True),
            sa.ForeignKey("chat_sessions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("role", sa.String(16), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("citations", pg.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("has_uncertainty", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("has_conflict", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("role IN ('user', 'assistant')", name="chat_message_role_valid"),
    )
    op.create_index("ix_chat_messages_session_id", "chat_messages", ["session_id"])


def downgrade():
    op.drop_table("chat_messages")
    op.drop_table("chat_sessions")
    op.drop_table("embedding_records")
    op.execute("DROP EXTENSION IF EXISTS vector CASCADE;")

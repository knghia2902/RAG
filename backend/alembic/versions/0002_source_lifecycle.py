"""Source lifecycle schema: sources, versions, jobs, runs, canonical records."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg

revision = "0002_source_lifecycle"
down_revision = '0001_access_control'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "sources",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True),
        sa.Column("dataset_id", pg.UUID(as_uuid=True), sa.ForeignKey("datasets.id"), nullable=False),
        sa.Column("logical_filename", sa.String(255), nullable=False),
        sa.Column("profile_id", sa.String(64), nullable=False),
        sa.Column("active_version_id", pg.UUID(as_uuid=True), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_sources_dataset_id", "sources", ["dataset_id"])
    op.create_index(
        "ix_sources_dataset_filename_active",
        "sources",
        ["dataset_id", "logical_filename"],
        unique=True,
        postgresql_where=sa.text("deleted_at IS NULL"),
    )

    op.create_table(
        "source_versions",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True),
        sa.Column("source_id", pg.UUID(as_uuid=True), sa.ForeignKey("sources.id"), nullable=False),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("content_hash", sa.String(64), nullable=False),
        sa.Column("storage_key", sa.String(255), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("mime_type", sa.String(64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("source_id", "version_number", name="uq_source_versions_num"),
        sa.CheckConstraint("version_number >= 1", name="positive_version_number"),
    )
    op.create_index("ix_source_versions_source_id", "source_versions", ["source_id"])

    op.create_foreign_key(
        "fk_sources_active_version",
        "sources",
        "source_versions",
        ["active_version_id"],
        ["id"],
    )

    op.create_table(
        "import_jobs",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True),
        sa.Column("source_version_id", pg.UUID(as_uuid=True), sa.ForeignKey("source_versions.id"), nullable=False),
        sa.Column("state", sa.String(32), nullable=False, server_default="queued"),
        sa.Column("attempt_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("max_attempts", sa.Integer(), nullable=False, server_default="3"),
        sa.Column("lease_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_code", sa.String(64), nullable=True),
        sa.Column("error_message", sa.String(1000), nullable=True),
        sa.Column("diagnostics", pg.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("state IN ('queued','processing','ready','failed')", name="job_state_valid"),
    )
    op.create_index("ix_import_jobs_source_version_id", "import_jobs", ["source_version_id"])

    op.create_table(
        "parse_runs",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True),
        sa.Column("source_version_id", pg.UUID(as_uuid=True), sa.ForeignKey("source_versions.id"), nullable=False),
        sa.Column("job_id", pg.UUID(as_uuid=True), sa.ForeignKey("import_jobs.id"), nullable=False),
        sa.Column("parser_name", sa.String(64), nullable=False),
        sa.Column("parser_version", sa.String(32), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="staged"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("status IN ('staged','published','failed')", name="parse_run_status_valid"),
    )
    op.create_index("ix_parse_runs_source_version_id", "parse_runs", ["source_version_id"])
    op.create_index("ix_parse_runs_job_id", "parse_runs", ["job_id"])

    op.create_table(
        "canonical_records",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True),
        sa.Column("parse_run_id", pg.UUID(as_uuid=True), sa.ForeignKey("parse_runs.id"), nullable=False),
        sa.Column("source_version_id", pg.UUID(as_uuid=True), sa.ForeignKey("source_versions.id"), nullable=False),
        sa.Column("dataset_id", pg.UUID(as_uuid=True), sa.ForeignKey("datasets.id"), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("locator_data", pg.JSONB(), nullable=False),
        sa.Column("content_text", sa.String(), nullable=False),
        sa.Column("record_metadata", pg.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("position >= 1", name="positive_position"),
    )
    op.create_index("ix_canonical_records_parse_run_id", "canonical_records", ["parse_run_id"])
    op.create_index("ix_canonical_records_source_version_id", "canonical_records", ["source_version_id"])
    op.create_index("ix_canonical_records_dataset_id", "canonical_records", ["dataset_id"])


def downgrade():
    op.drop_table("canonical_records")
    op.drop_table("parse_runs")
    op.drop_table("import_jobs")
    op.drop_constraint("fk_sources_active_version", "sources", type_="foreignkey")
    op.drop_table("source_versions")
    op.drop_index(
        "ix_sources_dataset_filename_active",
        table_name="sources",
        postgresql_where=sa.text("deleted_at IS NULL"),
    )
    op.drop_table("sources")

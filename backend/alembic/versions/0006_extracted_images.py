"""Extracted images persistence schema."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg

revision = "0006_extracted_images"
down_revision = "0005_incident_reports"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "extracted_images",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "source_version_id",
            pg.UUID(as_uuid=True),
            sa.ForeignKey("source_versions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "dataset_id",
            pg.UUID(as_uuid=True),
            sa.ForeignKey("datasets.id"),
            nullable=False,
        ),
        sa.Column("page_number", sa.Integer(), nullable=True),
        sa.Column("image_type", sa.String(32), server_default="embedded", nullable=False),
        sa.Column("storage_path", sa.String(512), nullable=False),
        sa.Column("mime_type", sa.String(64), server_default="image/png", nullable=False),
        sa.Column("width", sa.Integer(), nullable=True),
        sa.Column("height", sa.Integer(), nullable=True),
        sa.Column("size_bytes", sa.Integer(), server_default="0", nullable=False),
        sa.Column("caption", sa.String(500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_extracted_images_source_version_id", "extracted_images", ["source_version_id"])
    op.create_index("ix_extracted_images_dataset_id", "extracted_images", ["dataset_id"])
    op.create_index("ix_extracted_images_dataset_source", "extracted_images", ["dataset_id", "source_version_id"])
    op.create_index("ix_extracted_images_source_page", "extracted_images", ["source_version_id", "page_number"])


def downgrade():
    op.drop_table("extracted_images")

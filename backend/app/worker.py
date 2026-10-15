"""Worker task entrypoints and re-exports for ingestion pipeline."""
from uuid import UUID
from app.workers.tasks import *  # noqa: F401, F403
from app.workers.tasks import (
    process_ingestion_job,
    get_source_storage_path,
    get_extracted_images_storage_dir,
    index_source_version_task,
)


def import_source_version(source_version_id: UUID | str) -> None:
    """Direct helper to trigger ingestion for a source_version."""
    from app.database.session import SessionLocal
    from app.database.models import ImportJob
    with SessionLocal() as db:
        job = db.query(ImportJob).filter(ImportJob.source_version_id == UUID(str(source_version_id))).first()
        if job:
            process_ingestion_job(str(job.id))

from pathlib import Path
from uuid import UUID
from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.dependencies import get_account
from app.api.schemas import (
    EvidenceExcerptDTO,
    EvidencePreviewPage,
    IngestionJobDTO,
    SourceDTO,
    SourceLocatorDTO,
    SourcePage,
    SourceProfileDTO,
    UploadBatchResponseDTO,
    UploadResultItemDTO,
)
from app.api.users import mutation_manager
from app.auth.policy import allowed_dataset_ids, current_account
from app.database.datasets import recheck_response
from app.database.models import (
    Account,
    CanonicalRecord,
    Dataset,
    ImportJob,
    Source,
    SourceVersion,
)
from app.database.session import get_db
from app.database.sources import (
    reprocess_active_source,
    retry_failed_job,
    save_uploaded_source,
    tombstone_source,
)
from app.rag.parsers.profiles import PROFILES, get_profile

router = APIRouter(prefix="/api/v1", tags=["sources"])


@router.get("/datasets/{dataset_id}/sources/profiles", response_model=list[SourceProfileDTO])
def list_source_profiles(
    dataset_id: UUID,
    account: Account = Depends(get_account),
    db: Session = Depends(get_db),
):
    account = current_account(db, account)
    scope = allowed_dataset_ids(db, account)
    if dataset_id not in scope:
        raise HTTPException(404, "Không tìm thấy Dataset")
    recheck_response(db, account, {dataset_id})

    return [
        SourceProfileDTO(
            id=p.id,
            name=p.name,
            description=p.description,
            supported_formats=list(p.supported_formats),
            expected_fields=list(p.expected_fields),
            optional_fields=list(p.optional_fields),
        )
        for p in PROFILES.values()
    ]


@router.post("/admin/datasets/{dataset_id}/sources/upload", response_model=UploadBatchResponseDTO, status_code=201)
async def upload_sources(
    dataset_id: UUID,
    profile_id: str = Form(...),
    files: list[UploadFile] = File(...),
    actor: Account = Depends(mutation_manager),
    db: Session = Depends(get_db),
):
    dataset = db.get(Dataset, dataset_id)
    if dataset is None:
        raise HTTPException(404, "Không tìm thấy Dataset")

    try:
        profile = get_profile(profile_id)
    except ValueError as exc:
        raise HTTPException(400, f"Hồ sơ nguồn không hợp lệ: {profile_id}") from exc

    if not files:
        raise HTTPException(400, "Danh sách tệp tải lên không được để trống")

    if len(files) > 10:
        raise HTTPException(400, "Số lượng tệp tải lên vượt quá giới hạn tối đa (10 tệp/batch)")

    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
    items: list[UploadResultItemDTO] = []

    for file in files:
        filename = file.filename or "unknown"
        ext = Path(filename).suffix.lower()
        if ext not in profile.supported_formats:
            raise HTTPException(
                400,
                f"Định dạng tệp '{filename}' không được hỗ trợ bởi hồ sơ '{profile.name}'. "
                f"Định dạng hỗ trợ: {', '.join(profile.supported_formats)}",
            )

        content = await file.read()
        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(400, f"Kích thước tệp '{filename}' vượt quá giới hạn 50MB")

        mime_type = file.content_type or "application/octet-stream"
        source, version, job, is_new = save_uploaded_source(
            db=db,
            actor=actor,
            dataset_id=dataset_id,
            logical_filename=filename,
            profile_id=profile_id,
            content_bytes=content,
            mime_type=mime_type,
        )

        items.append(
            UploadResultItemDTO(
                filename=filename,
                source_id=source.id,
                version_number=version.version_number,
                status=job.state,
                job_id=job.id,
                is_duplicate=not is_new,
                message="Tải lên thành công" if is_new else "Tệp trùng lặp nội dung, giữ nguyên phiên bản hiện tại",
            )
        )

    return UploadBatchResponseDTO(items=items)


@router.get("/datasets/{dataset_id}/sources", response_model=SourcePage)
def list_sources(
    dataset_id: UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    account: Account = Depends(get_account),
    db: Session = Depends(get_db),
):
    account = current_account(db, account)
    scope = allowed_dataset_ids(db, account)
    if dataset_id not in scope:
        raise HTTPException(404, "Không tìm thấy Dataset")

    query = select(Source).where(
        Source.dataset_id == dataset_id,
        Source.deleted_at.is_(None),
    )
    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    sources = db.scalars(
        query.order_by(Source.created_at.desc(), Source.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()

    items: list[SourceDTO] = []
    for src in sources:
        active_ver_num: int | None = None
        if src.active_version_id is not None:
            active_ver = db.get(SourceVersion, src.active_version_id)
            if active_ver is not None:
                active_ver_num = active_ver.version_number

        latest_job = db.scalar(
            select(ImportJob)
            .join(SourceVersion, ImportJob.source_version_id == SourceVersion.id)
            .where(SourceVersion.source_id == src.id)
            .order_by(ImportJob.created_at.desc())
        )
        if latest_job is not None:
            status = latest_job.state
            err_msg = latest_job.error_message
        else:
            status = "ready" if src.active_version_id is not None else "queued"
            err_msg = None

        items.append(
            SourceDTO(
                id=src.id,
                dataset_id=src.dataset_id,
                logical_filename=src.logical_filename,
                profile_id=src.profile_id,
                active_version_id=src.active_version_id,
                active_version_number=active_ver_num,
                status=status,
                error_message=err_msg,
                created_at=src.created_at,
                updated_at=src.updated_at,
            )
        )

    result = SourcePage(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    )
    recheck_response(db, account, {dataset_id})
    return result


@router.get("/datasets/{dataset_id}/sources/{source_id}", response_model=SourceDTO)
def get_source_detail(
    dataset_id: UUID,
    source_id: UUID,
    account: Account = Depends(get_account),
    db: Session = Depends(get_db),
):
    account = current_account(db, account)
    scope = allowed_dataset_ids(db, account)
    if dataset_id not in scope:
        raise HTTPException(404, "Không tìm thấy Dataset")

    source = db.get(Source, source_id)
    if source is None or source.dataset_id != dataset_id or source.deleted_at is not None:
        raise HTTPException(404, "Không tìm thấy Nguồn dữ liệu")

    active_ver_num: int | None = None
    if source.active_version_id is not None:
        active_ver = db.get(SourceVersion, source.active_version_id)
        if active_ver is not None:
            active_ver_num = active_ver.version_number

    latest_job = db.scalar(
        select(ImportJob)
        .join(SourceVersion, ImportJob.source_version_id == SourceVersion.id)
        .where(SourceVersion.source_id == source.id)
        .order_by(ImportJob.created_at.desc())
    )
    if latest_job is not None:
        status = latest_job.state
        err_msg = latest_job.error_message
    else:
        status = "ready" if source.active_version_id is not None else "queued"
        err_msg = None

    result = SourceDTO(
        id=source.id,
        dataset_id=source.dataset_id,
        logical_filename=source.logical_filename,
        profile_id=source.profile_id,
        active_version_id=source.active_version_id,
        active_version_number=active_ver_num,
        status=status,
        error_message=err_msg,
        created_at=source.created_at,
        updated_at=source.updated_at,
    )
    recheck_response(db, account, {dataset_id})
    return result


@router.get("/datasets/{dataset_id}/sources/{source_id}/preview", response_model=EvidencePreviewPage)
def get_source_preview(
    dataset_id: UUID,
    source_id: UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    account: Account = Depends(get_account),
    db: Session = Depends(get_db),
):
    account = current_account(db, account)
    scope = allowed_dataset_ids(db, account)
    if dataset_id not in scope:
        raise HTTPException(404, "Không tìm thấy Dataset")

    source = db.get(Source, source_id)
    if (
        source is None
        or source.dataset_id != dataset_id
        or source.deleted_at is not None
        or source.active_version_id is None
    ):
        raise HTTPException(404, "Nguồn không khả dụng hoặc chưa có phiên bản sẵn sàng")

    active_version = db.get(SourceVersion, source.active_version_id)
    if active_version is None:
        raise HTTPException(404, "Nguồn không khả dụng hoặc chưa có phiên bản sẵn sàng")

    query = select(CanonicalRecord).where(
        CanonicalRecord.source_version_id == source.active_version_id
    )
    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    records = db.scalars(
        query.order_by(CanonicalRecord.position.asc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()

    items: list[EvidenceExcerptDTO] = []
    for record in records:
        loc_data = record.locator_data or {}
        locator = SourceLocatorDTO(
            source_id=source.id,
            source_version=active_version.version_number,
            page=loc_data.get("page"),
            section=loc_data.get("section"),
            sheet=loc_data.get("sheet"),
            row=loc_data.get("row"),
            event=loc_data.get("event"),
            record=loc_data.get("record"),
            line_start=loc_data.get("line_start"),
            line_end=loc_data.get("line_end"),
            json_path=loc_data.get("json_path"),
        )
        safe_metadata = {
            k: v
            for k, v in (record.record_metadata or {}).items()
            if "storage" not in k.lower() and "path" not in k.lower()
        }
        items.append(
            EvidenceExcerptDTO(
                id=record.id,
                position=record.position,
                text=record.content_text,
                locator=locator,
                metadata=safe_metadata,
            )
        )

    result = EvidencePreviewPage(
        source_id=source.id,
        version_number=active_version.version_number,
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    )
    recheck_response(db, account, {dataset_id})
    return result


@router.post("/admin/datasets/{dataset_id}/sources/{source_id}/retry", response_model=IngestionJobDTO)
def retry_source_job(
    dataset_id: UUID,
    source_id: UUID,
    actor: Account = Depends(mutation_manager),
    db: Session = Depends(get_db),
):
    job = retry_failed_job(db, actor, dataset_id, source_id)
    return IngestionJobDTO(
        id=job.id,
        source_version_id=job.source_version_id,
        state=job.state,
        attempt_count=job.attempt_count,
        error_code=job.error_code,
        error_message=job.error_message,
        diagnostics=job.diagnostics,
        created_at=job.created_at,
        updated_at=job.updated_at,
    )


@router.post("/admin/datasets/{dataset_id}/sources/{source_id}/reprocess", response_model=IngestionJobDTO)
def reprocess_source(
    dataset_id: UUID,
    source_id: UUID,
    actor: Account = Depends(mutation_manager),
    db: Session = Depends(get_db),
):
    job = reprocess_active_source(db, actor, dataset_id, source_id)
    return IngestionJobDTO(
        id=job.id,
        source_version_id=job.source_version_id,
        state=job.state,
        attempt_count=job.attempt_count,
        error_code=job.error_code,
        error_message=job.error_message,
        diagnostics=job.diagnostics,
        created_at=job.created_at,
        updated_at=job.updated_at,
    )


@router.delete("/admin/datasets/{dataset_id}/sources/{source_id}")
def delete_source(
    dataset_id: UUID,
    source_id: UUID,
    actor: Account = Depends(mutation_manager),
    db: Session = Depends(get_db),
):
    tombstone_source(db, actor, dataset_id, source_id)
    return {"message": "Đã xóa nguồn dữ liệu thành công"}

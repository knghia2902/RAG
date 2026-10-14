from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies import get_account
from app.api.schemas import (
    AnalyzeIncidentRequestDTO,
    CitationPreviewResponseDTO,
    IncidentAnalysisDetailDTO,
    IncidentHistoryItemDTO,
    SourceLocatorDTO,
)
from app.auth.policy import allowed_dataset_ids, current_account
from app.database.datasets import recheck_response
from app.database.models import Account, CanonicalRecord, Dataset, IncidentAnalysis, Source, SourceVersion
from app.database.session import get_db
from app.modules.log_analysis.service import IncidentAnalysisService
from app.modules.tickets.contracts import SystemEnum
from app.modules.tickets.service import TicketService

router = APIRouter(prefix="/api/v1/incidents", tags=["incidents"])


@router.post("/analyze", response_model=IncidentAnalysisDetailDTO, status_code=status.HTTP_200_OK)
def analyze_incident(
    payload: AnalyzeIncidentRequestDTO,
    account: Account = Depends(get_account),
    db: Session = Depends(get_db),
):
    """Analyze a logistics incident by Order ID."""
    service = IncidentAnalysisService(db=db)

    sys_enum = None
    if payload.system:
        try:
            sys_enum = SystemEnum(payload.system)
        except ValueError:
            sys_enum = None

    analysis_record, analysis_result = service.analyze_order(
        account=account,
        order_id=payload.order_id,
        description=payload.description,
        system=sys_enum,
        input_mode="quick_form",
    )

    return IncidentAnalysisDetailDTO(
        id=analysis_record.id,
        order_id=analysis_record.order_id,
        ticket_id=analysis_record.ticket_id,
        title=analysis_record.title,
        input_mode=analysis_record.input_mode,
        summary=analysis_result.summary,
        classification=analysis_record.classification_json,
        timeline=analysis_record.timeline_json,
        hypotheses=analysis_record.analysis_json.get("hypotheses", []),
        missing_information=analysis_record.analysis_json.get("missing_information", []),
        recommended_actions=analysis_record.analysis_json.get("recommended_actions", []),
        citations=analysis_record.citations_json,
        created_at=analysis_record.created_at,
    )


@router.post("/upload-ticket", status_code=status.HTTP_200_OK)
async def upload_ticket_file(
    file: UploadFile = File(...),
    account: Account = Depends(get_account),
    db: Session = Depends(get_db),
):
    """Upload and validate ticket batch file (CSV or JSON), then trigger analysis."""
    content = await file.read()
    filename = file.filename or "ticket.json"

    ticket_service = TicketService()
    try:
        val_result = ticket_service.process_uploaded_file(content, filename)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


    if not val_result.is_valid:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "message": f"Tệp ticket chứa {len(val_result.errors)} lỗi cú pháp hoặc cấu trúc.",
                "total_rows": val_result.total_rows,
                "errors": [err.model_dump() for err in val_result.errors],
            },
        )

    if not val_result.tickets:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tệp ticket hợp lệ nhưng không chứa dòng dữ liệu nào.",
        )

    # Automatically analyze the first ticket in the batch
    first_ticket = val_result.tickets[0]
    service = IncidentAnalysisService(db=db)
    analysis_record, analysis_result = service.analyze_order(
        account=account,
        order_id=first_ticket.order_id,
        description=first_ticket.description,
        system=first_ticket.system,
        ticket_info=first_ticket,
        input_mode="ticket_upload",
    )

    detail_dto = IncidentAnalysisDetailDTO(
        id=analysis_record.id,
        order_id=analysis_record.order_id,
        ticket_id=analysis_record.ticket_id,
        title=analysis_record.title,
        input_mode=analysis_record.input_mode,
        summary=analysis_result.summary,
        classification=analysis_record.classification_json,
        timeline=analysis_record.timeline_json,
        hypotheses=analysis_record.analysis_json.get("hypotheses", []),
        missing_information=analysis_record.analysis_json.get("missing_information", []),
        recommended_actions=analysis_record.analysis_json.get("recommended_actions", []),
        citations=analysis_record.citations_json,
        created_at=analysis_record.created_at,
    )

    return {
        "message": f"Tiếp nhận thành công {val_result.total_rows} phiếu ticket.",
        "total_tickets": val_result.total_rows,
        "analyzed_ticket_id": first_ticket.ticket_id,
        "analysis": detail_dto.model_dump(),
    }


@router.get("/history", response_model=list[IncidentHistoryItemDTO])
def list_incident_history(
    account: Account = Depends(get_account),
    db: Session = Depends(get_db),
):
    """List past incident analysis runs for the current user (or all if admin)."""
    account = current_account(db, account)

    stmt = select(IncidentAnalysis).order_by(IncidentAnalysis.created_at.desc())
    if account.role != "admin":
        stmt = stmt.where(IncidentAnalysis.account_id == account.id)

    records = db.scalars(stmt).all()

    items = []
    for r in records:
        cls_data = r.classification_json or {}
        items.append(
            IncidentHistoryItemDTO(
                id=r.id,
                order_id=r.order_id,
                ticket_id=r.ticket_id,
                title=r.title,
                input_mode=r.input_mode,
                error_group=cls_data.get("error_group", "N/A"),
                primary_system=cls_data.get("primary_system", "N/A"),
                suggested_priority=cls_data.get("suggested_priority", "N/A"),
                created_at=r.created_at,
            )
        )
    return items


@router.get("/{analysis_id}", response_model=IncidentAnalysisDetailDTO)
def get_incident_analysis_detail(
    analysis_id: UUID,
    account: Account = Depends(get_account),
    db: Session = Depends(get_db),
):
    """Retrieve details of an incident analysis run with Live Scope Recheck."""
    account = current_account(db, account)
    analysis = db.get(IncidentAnalysis, analysis_id)
    if not analysis:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy hồ sơ phân tích sự cố.")

    # Authorization / IDOR check
    if account.role != "admin" and analysis.account_id != account.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy hồ sơ phân tích sự cố.")

    # Live Scope Recheck: inspect dataset IDs in citations
    referenced_dataset_ids = set()
    for cit in analysis.citations_json or []:
        raw_ds = cit.get("dataset_id")
        if raw_ds:
            try:
                referenced_dataset_ids.add(UUID(str(raw_ds)))
            except Exception:
                pass

    if referenced_dataset_ids:
        allowed = allowed_dataset_ids(db, account)
        if any(ds not in allowed for ds in referenced_dataset_ids):
            raise HTTPException(
                status.HTTP_403_FORBIDDEN,
                "Quyền truy cập nguồn dữ liệu đã thay đổi hoặc bị thu hồi.",
            )
        recheck_response(db, account, referenced_dataset_ids)

    return IncidentAnalysisDetailDTO(
        id=analysis.id,
        order_id=analysis.order_id,
        ticket_id=analysis.ticket_id,
        title=analysis.title,
        input_mode=analysis.input_mode,
        summary=analysis.analysis_json.get("summary", ""),
        classification=analysis.classification_json,
        timeline=analysis.timeline_json,
        hypotheses=analysis.analysis_json.get("hypotheses", []),
        missing_information=analysis.analysis_json.get("missing_information", []),
        recommended_actions=analysis.analysis_json.get("recommended_actions", []),
        citations=analysis.citations_json,
        created_at=analysis.created_at,
    )


@router.get("/citations/{citation_id}/preview", response_model=CitationPreviewResponseDTO)
def preview_incident_citation(
    citation_id: int,
    dataset_id: UUID = Query(...),
    source_id: Optional[UUID] = Query(None),
    source_filename: Optional[str] = Query(None),
    line: Optional[int] = Query(None),
    account: Account = Depends(get_account),
    db: Session = Depends(get_db),
):
    """Preview citation excerpt with real-time Live Scope Recheck (D-05, AUTH-04)."""
    account = current_account(db, account)

    # 1. Live Scope Recheck
    allowed = allowed_dataset_ids(db, account)
    if dataset_id not in allowed:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            "Quyền truy cập nguồn dữ liệu đã thay đổi hoặc bị thu hồi.",
        )
    recheck_response(db, account, {dataset_id})

    # 2. Dataset & Source details
    dataset = db.get(Dataset, dataset_id)
    dataset_name = dataset.name if dataset else "Dataset"

    source = None
    if source_id:
        source = db.get(Source, source_id)
    elif source_filename:
        source = db.scalars(
            select(Source)
            .where(Source.dataset_id == dataset_id, Source.logical_filename == source_filename)
        ).first()

    if not source or source.deleted_at is not None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Nguồn dữ liệu không tồn tại hoặc đã bị xóa.")

    version = db.get(SourceVersion, source.active_version_id)
    version_num = version.version_number if version else 1

    rec = db.scalars(
        select(CanonicalRecord)
        .where(CanonicalRecord.source_version_id == source.active_version_id)
        .order_by(CanonicalRecord.position.asc())
        .limit(1)
    ).first()

    loc_dto = SourceLocatorDTO(
        source_id=source.id,
        source_version=version_num,
        line_start=line or (rec.locator_data.get("line_start") if rec and rec.locator_data else None),
        line_end=line or (rec.locator_data.get("line_end") if rec and rec.locator_data else None),
    )

    return CitationPreviewResponseDTO(
        citation_index=citation_id,
        dataset_id=dataset_id,
        dataset_name=dataset_name,
        source_id=source.id,
        logical_filename=source.logical_filename,
        version_number=version_num,
        locator=loc_dto,
        excerpt_text=rec.content_text if rec else "Không có đoạn trích khả dụng.",
    )

import io
from typing import Any
import uuid

from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.api.dependencies import get_account
from app.auth.policy import allowed_dataset_ids, has_capability
from app.database.models import Account
from app.database.session import get_db
from app.modules.reports.contracts import ReportDetailDTO, ReportFilterDTO
from app.modules.reports.service import ReportService

router = APIRouter(prefix="/api/v1/reports", tags=["reports"])


@router.post("/generate", response_model=ReportDetailDTO, status_code=status.HTTP_200_OK)
def generate_report(
    filter_dto: ReportFilterDTO,
    account: Account = Depends(get_account),
    db: Session = Depends(get_db),
):
    """Generates an on-demand incident & operational report with deterministic metrics and AI narrative."""
    if not has_capability(account, "report.create"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tài khoản không có quyền tạo báo cáo",
        )

    allowed_ds = allowed_dataset_ids(db, account)
    report = ReportService.generate_report(
        db=db,
        account_id=account.id,
        filter_dto=filter_dto,
        allowed_dataset_ids=allowed_ds,
    )

    return ReportService.get_report_detail(
        db=db,
        report_id=report.id,
        account_id=account.id,
        role=account.role,
        allowed_dataset_ids=allowed_ds,
    )


@router.get("/history", response_model=list[dict[str, Any]], status_code=status.HTTP_200_OK)
def list_report_history(
    account: Account = Depends(get_account),
    db: Session = Depends(get_db),
):
    """Lists report generation history subject to current dataset permissions."""
    if not has_capability(account, "report.read"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tài khoản không có quyền xem báo cáo",
        )

    allowed_ds = allowed_dataset_ids(db, account)
    return ReportService.list_reports(
        db=db,
        account_id=account.id,
        role=account.role,
        allowed_dataset_ids=allowed_ds,
    )


@router.get("/{report_id}", response_model=ReportDetailDTO, status_code=status.HTTP_200_OK)
def get_report_detail(
    report_id: uuid.UUID,
    account: Account = Depends(get_account),
    db: Session = Depends(get_db),
):
    """Retrieves report detail and metrics with Live Scope Recheck (AUTH-04, REP-06)."""
    if not has_capability(account, "report.read"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tài khoản không có quyền xem báo cáo",
        )

    allowed_ds = allowed_dataset_ids(db, account)
    return ReportService.get_report_detail(
        db=db,
        report_id=report_id,
        account_id=account.id,
        role=account.role,
        allowed_dataset_ids=allowed_ds,
    )


@router.get("/{report_id}/pdf", status_code=status.HTTP_200_OK)
def download_report_pdf(
    report_id: uuid.UUID,
    account: Account = Depends(get_account),
    db: Session = Depends(get_db),
):
    """Renders and downloads printable Vietnamese A4 PDF report with Live Scope Recheck."""
    if not has_capability(account, "report.read"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tài khoản không có quyền tải báo cáo",
        )

    allowed_ds = allowed_dataset_ids(db, account)
    pdf_bytes, filename = ReportService.get_report_pdf(
        db=db,
        report_id=report_id,
        account_id=account.id,
        role=account.role,
        allowed_dataset_ids=allowed_ds,
    )

    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Cache-Control": "no-store, no-cache, must-revalidate",
        },
    )


@router.get("/{report_id}/provenance", response_model=list[dict[str, Any]], status_code=status.HTTP_200_OK)
def get_report_provenance(
    report_id: uuid.UUID,
    account: Account = Depends(get_account),
    db: Session = Depends(get_db),
):
    """Inspects dataset and source file provenance snapshot for a specific report."""
    if not has_capability(account, "report.read"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tài khoản không có quyền xem dữ liệu tham chiếu",
        )

    allowed_ds = allowed_dataset_ids(db, account)
    report = ReportService.get_report(
        db=db,
        report_id=report_id,
        account_id=account.id,
        role=account.role,
        allowed_dataset_ids=allowed_ds,
    )
    return report.provenance_json

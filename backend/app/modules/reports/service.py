from datetime import date, datetime
from typing import Any, Optional
import uuid

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.models import CanonicalRecord, IncidentAnalysis, Report, Source, SourceVersion
from app.llm.contracts import LLMProvider
from app.modules.reports.aggregator import (
    VN_TZ,
    aggregate_report_metrics,
    compute_period_bounds,
)
from app.modules.reports.contracts import (
    PeriodTypeEnum,
    ReportDetailDTO,
    ReportFilterDTO,
    ReportMetricsDTO,
    ReportNarrativeDTO,
)
from app.modules.reports.narrative import ReportNarrativeSynthesizer
from app.modules.reports.pdf_generator import ReportPDFGenerator


class ReportService:
    @staticmethod
    def get_period_bounds(
        period_type: PeriodTypeEnum,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        now: Optional[datetime] = None,
    ) -> tuple[datetime, datetime]:
        return compute_period_bounds(period_type, start_date, end_date, now)

    @staticmethod
    def compute_metrics(
        incident_analyses: list[Any],
        canonical_records: list[Any],
    ) -> ReportMetricsDTO:
        return aggregate_report_metrics(incident_analyses, canonical_records)

    @staticmethod
    def generate_report(
        db: Session,
        account_id: uuid.UUID,
        filter_dto: ReportFilterDTO,
        allowed_dataset_ids: set[uuid.UUID],
        llm_provider: Optional[LLMProvider] = None,
    ) -> Report:
        # 1. Dataset permission check
        requested_ids = filter_dto.dataset_ids
        if requested_ids:
            for did in requested_ids:
                if did not in allowed_dataset_ids:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Bạn không có quyền truy cập một hoặc nhiều dataset yêu cầu",
                    )
            target_dataset_ids = list(requested_ids)
        else:
            if not allowed_dataset_ids:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Tài khoản không được cấp quyền truy cập dataset nào",
                )
            target_dataset_ids = list(allowed_dataset_ids)

        # 2. Timezone bounds
        start_time, end_time = compute_period_bounds(
            filter_dto.period_type,
            filter_dto.start_date,
            filter_dto.end_date,
        )

        # 3. Query canonical records and incident analyses in period & dataset scope
        canonical_records = db.scalars(
            select(CanonicalRecord)
            .where(
                CanonicalRecord.dataset_id.in_(target_dataset_ids),
                CanonicalRecord.created_at >= start_time,
                CanonicalRecord.created_at <= end_time,
            )
        ).all()

        incident_analyses = db.scalars(
            select(IncidentAnalysis)
            .where(
                IncidentAnalysis.created_at >= start_time,
                IncidentAnalysis.created_at <= end_time,
            )
        ).all()

        # 4. Deterministic metrics computation
        metrics_dto = aggregate_report_metrics(incident_analyses, canonical_records)

        # 5. Provenance snapshot
        provenance_sources: list[dict[str, Any]] = []
        source_version_ids = {r.source_version_id for r in canonical_records if r.source_version_id}
        if source_version_ids:
            sv_rows = db.execute(
                select(SourceVersion.id, SourceVersion.version_number, Source.logical_filename, Source.dataset_id)
                .join(Source, SourceVersion.source_id == Source.id)
                .where(SourceVersion.id.in_(source_version_ids))
            ).all()
            for sv_id, v_num, filename, ds_id in sv_rows:
                provenance_sources.append({
                    "source_id": str(sv_id),
                    "version_number": v_num,
                    "filename": filename,
                    "dataset_id": str(ds_id),
                })

        if not provenance_sources:
            for ds_id in target_dataset_ids:
                provenance_sources.append({
                    "source_id": str(uuid.uuid4()),
                    "version_number": 1,
                    "filename": f"dataset_{str(ds_id)[:8]}_records",
                    "dataset_id": str(ds_id),
                })

        # 6. LLM Narrative Synthesis with safe secret masking & deterministic fallback
        synthesizer = ReportNarrativeSynthesizer(llm_provider)
        samples = [
            {
                "order_id": getattr(inc, "order_id", ""),
                "system": (getattr(inc, "classification_json", {}) or {}).get("primary_system", ""),
                "error_group": (getattr(inc, "classification_json", {}) or {}).get("error_group", ""),
            }
            for inc in incident_analyses[:5]
        ]

        period_label_map = {
            PeriodTypeEnum.DAILY: "ngày",
            PeriodTypeEnum.WEEKLY: "tuần",
            PeriodTypeEnum.MONTHLY: "tháng",
            PeriodTypeEnum.CUSTOM: "khoảng tùy chọn",
        }
        period_label = period_label_map.get(filter_dto.period_type, "kỳ")
        narrative_dto = synthesizer.synthesize_narrative(
            metrics=metrics_dto,
            period_description=f"báo cáo sự cố {period_label}",
            incident_samples=samples,
        )

        now_vn = datetime.now(tz=VN_TZ)
        title = f"Báo cáo sự cố {period_label} - {now_vn.strftime('%d/%m/%Y %H:%M')}"

        # 7. Persist to database
        report = Report(
            account_id=account_id,
            title=title,
            period_type=filter_dto.period_type.value,
            start_time=start_time,
            end_time=end_time,
            dataset_ids=[str(did) for did in target_dataset_ids],
            metrics_json=metrics_dto.model_dump(),
            narrative_json=narrative_dto.model_dump(),
            provenance_json=provenance_sources,
        )
        db.add(report)
        db.commit()
        db.refresh(report)

        return report

    @staticmethod
    def get_report(
        db: Session,
        report_id: uuid.UUID,
        account_id: uuid.UUID,
        role: str,
        allowed_dataset_ids: set[uuid.UUID],
    ) -> Report:
        report = db.get(Report, report_id)
        if not report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Không tìm thấy báo cáo yêu cầu",
            )

        # IDOR check: Admin or report creator only
        if role != "admin" and report.account_id != account_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Bạn không có quyền truy cập báo cáo này",
            )

        # Live Scope Recheck (AUTH-04, REP-06):
        # Even if created in the past, verify current permissions for every dataset in report.dataset_ids
        if role != "admin":
            report_datasets = [uuid.UUID(did) for did in report.dataset_ids]
            for did in report_datasets:
                if did not in allowed_dataset_ids:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Quyền truy cập vào dữ liệu báo cáo đã bị thu hồi hoặc bạn không có quyền xem báo cáo này",
                    )

        return report

    @classmethod
    def get_report_detail(
        cls,
        db: Session,
        report_id: uuid.UUID,
        account_id: uuid.UUID,
        role: str,
        allowed_dataset_ids: set[uuid.UUID],
    ) -> ReportDetailDTO:
        report = cls.get_report(db, report_id, account_id, role, allowed_dataset_ids)

        return ReportDetailDTO(
            id=report.id,
            title=report.title,
            period_type=PeriodTypeEnum(report.period_type),
            start_time=report.start_time,
            end_time=report.end_time,
            timezone="Asia/Ho_Chi_Minh",
            dataset_ids=report.dataset_ids,
            metrics=ReportMetricsDTO.model_validate(report.metrics_json),
            narrative=ReportNarrativeDTO.model_validate(report.narrative_json),
            provenance_sources=report.provenance_json,
            created_at=report.created_at,
        )

    @classmethod
    def get_report_pdf(
        cls,
        db: Session,
        report_id: uuid.UUID,
        account_id: uuid.UUID,
        role: str,
        allowed_dataset_ids: set[uuid.UUID],
    ) -> tuple[bytes, str]:
        detail = cls.get_report_detail(db, report_id, account_id, role, allowed_dataset_ids)
        generator = ReportPDFGenerator()
        pdf_bytes = generator.generate_pdf(detail)
        filename = f"bao_cao_su_co_{str(report_id)[:8]}.pdf"
        return pdf_bytes, filename

    @staticmethod
    def list_reports(
        db: Session,
        account_id: uuid.UUID,
        role: str,
        allowed_dataset_ids: set[uuid.UUID],
    ) -> list[dict[str, Any]]:
        query = select(Report).order_by(Report.created_at.desc())
        if role != "admin":
            query = query.where(Report.account_id == account_id)

        reports = db.scalars(query).all()
        results: list[dict[str, Any]] = []

        for r in reports:
            # Live Scope filter: omit reports whose datasets have been revoked
            if role != "admin":
                has_revoked = any(uuid.UUID(did) not in allowed_dataset_ids for did in r.dataset_ids)
                if has_revoked:
                    continue

            metrics = r.metrics_json or {}
            results.append({
                "id": str(r.id),
                "title": r.title,
                "period_type": r.period_type,
                "start_time": r.start_time.isoformat(),
                "end_time": r.end_time.isoformat(),
                "total_incidents": metrics.get("total_incidents", 0),
                "total_tickets": metrics.get("total_tickets", 0),
                "created_at": r.created_at.isoformat(),
            })

        return results

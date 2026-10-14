import re
from typing import Optional
from uuid import UUID
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.policy import allowed_dataset_ids, current_account
from app.database.models import Account, CanonicalRecord, IncidentAnalysis, Source, SourceVersion
from app.modules.log_analysis.contracts import CorrelatedOrderLogs, IncidentAnalysisResultDTO
from app.modules.log_analysis.correlator import CrossSystemLogCorrelator
from app.modules.log_analysis.reasoner import IncidentReasoner
from app.modules.log_analysis.sop_matcher import SOPMatcher
from app.modules.tickets.contracts import SystemEnum, TicketImportRow
from app.providers import get_embedding_provider, get_llm_provider
from app.rag.contracts import AuthorizedScope


class IncidentAnalysisService:
    """Service orchestrating cross-system log correlation, SOP matching, and structured incident analysis."""

    def __init__(
        self,
        db: Session,
        correlator: Optional[CrossSystemLogCorrelator] = None,
        sop_matcher: Optional[SOPMatcher] = None,
        reasoner: Optional[IncidentReasoner] = None,
    ):
        self.db = db
        self.correlator = correlator or CrossSystemLogCorrelator()
        self.sop_matcher = sop_matcher or SOPMatcher(embedding_provider=get_embedding_provider(), db=db)
        self.reasoner = reasoner or IncidentReasoner(llm_provider=get_llm_provider())

    def analyze_order(
        self,
        account: Account,
        order_id: str,
        description: Optional[str] = None,
        system: Optional[SystemEnum] = None,
        ticket_info: Optional[TicketImportRow] = None,
        input_mode: str = "quick_form",
    ) -> tuple[IncidentAnalysis, IncidentAnalysisResultDTO]:
        """Execute full incident analysis for an order within authorized datasets.

        Args:
            account: Current authenticated user.
            order_id: Order identifier.
            description: Optional incident description.
            system: Optional system hint.
            ticket_info: Optional ticket data if imported from file.
            input_mode: "quick_form" or "ticket_upload".

        Returns:
            Tuple of (persisted IncidentAnalysis record, IncidentAnalysisResultDTO).
        """
        clean_order_id = order_id.strip()
        if not re.match(r"^[A-Za-z0-9_-]{3,64}$", clean_order_id):
            raise HTTPException(400, "Mã đơn hàng không hợp lệ (yêu cầu 3-64 ký tự chữ, số, gạch ngang).")

        account = current_account(self.db, account)
        allowed_ids = allowed_dataset_ids(self.db, account)
        if not allowed_ids:
            raise HTTPException(403, "Tài khoản chưa được cấp quyền truy cập bất kỳ dataset nào.")

        # 1. Fetch relevant canonical records for order_id within authorized datasets
        records_stmt = (
            select(CanonicalRecord, Source, SourceVersion)
            .join(SourceVersion, CanonicalRecord.source_version_id == SourceVersion.id)
            .join(Source, SourceVersion.source_id == Source.id)
            .where(
                CanonicalRecord.dataset_id.in_(allowed_ids),
                Source.deleted_at.is_(None),
                Source.active_version_id == SourceVersion.id,
                CanonicalRecord.content_text.op("~*")(rf"\m{clean_order_id}\M"),
            )
            .order_by(CanonicalRecord.position.asc())
            .limit(200)
        )
        db_records = self.db.execute(records_stmt).all()

        raw_records = []
        for rec, src, ver in db_records:
            loc = rec.locator_data or {}
            raw_records.append({
                "text": rec.content_text,
                "filename": src.logical_filename,
                "line": loc.get("line_start") or loc.get("row") or loc.get("page") or 1,
                "dataset_id": str(rec.dataset_id),
                "source_id": str(src.id),
            })

        # 2. Correlate logs across systems
        correlated_logs: CorrelatedOrderLogs = self.correlator.correlate_order(clean_order_id, raw_records)

        # 3. Match SOP and incident precedents
        scope = AuthorizedScope(dataset_ids=tuple(allowed_ids))
        query_text = f"{clean_order_id} {description or ''} {system.value if system else ''}".strip()
        sop_chunks = self.sop_matcher.match_sop_and_precedents(
            error_description=query_text,
            authorized_scope=scope,
            db=self.db,
            top_k=5,
        )

        # 4. Reason and generate structured analysis
        analysis_result = self.reasoner.analyze_incident(
            order_id=clean_order_id,
            correlated_logs=correlated_logs,
            sop_evidences=sop_chunks,
            ticket_info=ticket_info,
        )

        # Enrich citations with dataset_id if matched from raw_records
        source_to_dataset: dict[str, str] = {
            r["filename"]: r["dataset_id"] for r in raw_records if "dataset_id" in r
        }
        for cit in analysis_result.citations:
            if cit.get("source") in source_to_dataset and not cit.get("dataset_id"):
                cit["dataset_id"] = source_to_dataset[cit["source"]]

        # 5. Persist analysis to database
        analysis_record = IncidentAnalysis(
            account_id=account.id,
            order_id=clean_order_id,
            ticket_id=ticket_info.ticket_id if ticket_info else None,
            input_mode=input_mode,
            title=f"Phân tích sự cố đơn hàng {clean_order_id}",
            classification_json=analysis_result.classification.model_dump(),
            timeline_json=[ev.model_dump() for ev in analysis_result.timeline],
            analysis_json={
                "hypotheses": [h.model_dump() for h in analysis_result.hypotheses],
                "missing_information": analysis_result.missing_information,
                "recommended_actions": [a.model_dump() for a in analysis_result.recommended_actions],
                "summary": analysis_result.summary,
            },
            citations_json=analysis_result.citations,
        )
        self.db.add(analysis_record)
        self.db.commit()
        self.db.refresh(analysis_record)

        return analysis_record, analysis_result

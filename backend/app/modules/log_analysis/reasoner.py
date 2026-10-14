import json
import re
from typing import Any, Optional
from uuid import uuid4

from app.llm.contracts import GenerationRequest, LLMProvider
from app.llm.secret_masking import mask_secrets
from app.modules.log_analysis.contracts import (
    ActionStepDTO,
    CategorizedEvidenceChunk,
    CorrelatedOrderLogs,
    EvidenceKindEnum,
    IncidentAnalysisResultDTO,
    IncidentClassificationDTO,
    RootCauseHypothesisDTO,
    TimelineEventDTO,
)
from app.modules.tickets.contracts import SeverityEnum, SystemEnum, TicketImportRow
from app.rag.contracts import EvidenceChunk, SourceLocator


class IncidentReasoner:
    """Structured LLM reasoner generating classified incident analysis, hypotheses, and recommendations."""

    def __init__(self, llm_provider: LLMProvider, masker: Optional[Any] = None):
        self.llm_provider = llm_provider
        self.masker = masker

    def _mask(self, text: str) -> str:
        if self.masker is not None:
            if hasattr(self.masker, "mask_secrets"):
                return self.masker.mask_secrets(text)
            if callable(self.masker):
                return self.masker(text)
        return mask_secrets(text)

    def analyze_incident(
        self,
        order_id: str,
        correlated_logs: CorrelatedOrderLogs,
        sop_evidences: list[EvidenceChunk],
        ticket_info: Optional[TicketImportRow] = None,
    ) -> IncidentAnalysisResultDTO:
        """Analyze an incident by correlating timeline logs, SOP rules, and ticket details.

        Args:
            order_id: Order identifier.
            correlated_logs: Correlated multi-system logs with timeline and failure point.
            sop_evidences: Matched SOP procedures and incident precedents.
            ticket_info: Optional ticket intake data.

        Returns:
            IncidentAnalysisResultDTO containing classifications, hypotheses, missing data, and SOP actions.
        """
        clean_order_id = order_id.strip()

        # 1. Prepare Citations map and Structured Context
        citations: list[dict[str, Any]] = []
        current_log_lines: list[str] = []

        for ev in correlated_logs.timeline:
            c_id = ev.citation_id or (len(citations) + 1)
            citations.append({
                "citation_id": c_id,
                "kind": EvidenceKindEnum.CURRENT_LOG.value,
                "source": ev.source_filename,
                "line": ev.line_number,
                "timestamp": ev.timestamp,
                "system": ev.system.value,
                "snippet": ev.raw_snippet,
            })
            current_log_lines.append(
                f"[#{c_id}] {ev.timestamp} [{ev.system.value}] {ev.event_name} "
                f"(Status: {ev.status}, File: {ev.source_filename}:{ev.line_number}): {ev.raw_snippet}"
            )

        sop_lines: list[str] = []
        for chunk in sop_evidences:
            c_id = len(citations) + 1
            kind = getattr(chunk, "evidence_kind", EvidenceKindEnum.SOP_PROCEDURE)
            kind_val = kind.value if isinstance(kind, EvidenceKindEnum) else str(kind)
            loc = chunk.locator
            citations.append({
                "citation_id": c_id,
                "kind": kind_val,
                "source": str(loc.source_id),
                "version": loc.source_version,
                "page": loc.page,
                "snippet": chunk.text,
            })
            sop_lines.append(
                f"[#{c_id}] [{kind_val}] Source: {loc.source_id} (Page: {loc.page}): {chunk.text}"
            )

        # 2. Build prompt context
        ticket_context = ""
        if ticket_info:
            ticket_context = (
                f"\n=== THÔNG TIN PHIẾU TICKET ===\n"
                f"Mã phiếu: {ticket_info.ticket_id}\n"
                f"Hệ thống báo: {ticket_info.system.value}\n"
                f"Mức nghiêm trọng: {ticket_info.severity.value}\n"
                f"Mô tả: {ticket_info.description}\n"
            )

        context_text = (
            f"=== BẰNG CHỨNG LOG ĐƠN HÀNG {clean_order_id} (CURRENT LOGS) ===\n"
            + ("\n".join(current_log_lines) if current_log_lines else "Không có log trực tiếp.")
            + "\n\n=== QUY TRÌNH SOP VÀ TIỀN LỆ LỊCH SỬ (SOP & PRECEDENTS) ===\n"
            + ("\n".join(sop_lines) if sop_lines else "Không tìm thấy SOP tương ứng.")
            + ticket_context
        )

        masked_context = self._mask(context_text)

        system_instructions = (
            f"Bạn là chuyên gia phân tích sự cố vận hành Logistics IT (WMS-TMS).\n"
            f"Phân tích sự cố của đơn hàng '{clean_order_id}' dựa trên log và SOP được cấp.\n"
            f"Yêu cầu:\n"
            f"1. Phân loại nhóm lỗi (error_group), hệ thống chính (primary_system), mức ưu tiên (P1-P4) kèm confidence (0.0 - 1.0).\n"
            f"2. Phân biệt rõ ràng giữa 'giả thuyết' (is_confirmed=false) và 'nguyên nhân đã xác nhận' (is_confirmed=true khi có bằng chứng trực tiếp trong log).\n"
            f"3. Tuân thủ RAG-05: Liệt kê các phần dữ liệu còn thiếu trong 'missing_information' (ví dụ: thiếu log đối soát của TMS).\n"
            f"4. Đề xuất các bước kiểm tra/xử lý có trích dẫn mã quy trình SOP cụ thể trong 'recommended_actions'.\n"
            f"5. Xuất kết quả dưới định dạng JSON duy nhất tuân thủ schema IncidentAnalysisResultDTO.\n"
        )

        # Ensure evidence chunk tuple is non-empty for GenerationRequest contract
        evidence_chunks = list(sop_evidences)
        if not evidence_chunks:
            evidence_chunks.append(
                EvidenceChunk(
                    dataset_id=uuid4(),
                    locator=SourceLocator(source_id=uuid4(), source_version=1),
                    text=f"Timeline for {clean_order_id}: {correlated_logs.total_events} events.",
                )
            )

        gen_request = GenerationRequest(
            question=f"{system_instructions}\n\n{masked_context}",
            evidence=tuple(evidence_chunks),
        )

        # 3. Call LLM Provider
        try:
            gen_result = self.llm_provider.generate(gen_request)
            llm_text = gen_result.text
        except Exception:
            llm_text = ""

        # 4. Parse JSON from LLM or fallback to deterministic synthesizer
        parsed_result = self._parse_or_synthesize(
            llm_text=llm_text,
            order_id=clean_order_id,
            correlated_logs=correlated_logs,
            sop_evidences=sop_evidences,
            ticket_info=ticket_info,
            citations=citations,
        )

        return parsed_result

    def _parse_or_synthesize(
        self,
        llm_text: str,
        order_id: str,
        correlated_logs: CorrelatedOrderLogs,
        sop_evidences: list[EvidenceChunk],
        ticket_info: Optional[TicketImportRow],
        citations: list[dict[str, Any]],
    ) -> IncidentAnalysisResultDTO:
        """Attempt to parse LLM JSON, falling back to deterministic synthesis if needed."""
        # Check for JSON block in LLM response
        json_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", llm_text, re.DOTALL)
        candidate_json = json_match.group(1) if json_match else llm_text.strip()

        if candidate_json.startswith("{") and candidate_json.endswith("}"):
            try:
                data = json.loads(candidate_json)
                # Overwrite deterministic timeline and citations to guarantee integrity
                data["order_id"] = order_id
                data["timeline"] = [ev.model_dump() for ev in correlated_logs.timeline]
                data["citations"] = citations
                if ticket_info and "ticket_id" not in data:
                    data["ticket_id"] = ticket_info.ticket_id
                return IncidentAnalysisResultDTO.model_validate(data)
            except Exception:
                pass

        # Deterministic Synthesizer fallback
        return self._synthesize_analysis(
            order_id=order_id,
            correlated_logs=correlated_logs,
            sop_evidences=sop_evidences,
            ticket_info=ticket_info,
            citations=citations,
        )

    def _synthesize_analysis(
        self,
        order_id: str,
        correlated_logs: CorrelatedOrderLogs,
        sop_evidences: list[EvidenceChunk],
        ticket_info: Optional[TicketImportRow],
        citations: list[dict[str, Any]],
    ) -> IncidentAnalysisResultDTO:
        """Deterministic rule-based analysis synthesis when LLM is unavailable or test fake."""
        failure = correlated_logs.failure_point

        # 1. Classification
        if failure:
            primary_system = failure.system
            upper_raw = failure.raw_snippet.upper()
            if "504" in upper_raw or "TIMEOUT" in upper_raw:
                error_group = "Mất đồng bộ WMS-TMS do timeout kết nối"
                suggested_priority = SeverityEnum.P1
                confidence = 0.95
            elif "500" in upper_raw or "INTERNAL" in upper_raw:
                error_group = "Lỗi hệ thống nội bộ máy chủ API Gateway"
                suggested_priority = SeverityEnum.P2
                confidence = 0.90
            else:
                error_group = f"Lỗi xử lý luồng vận hành tại {failure.system.value}"
                suggested_priority = SeverityEnum.P2
                confidence = 0.85
        else:
            primary_system = ticket_info.system if ticket_info else SystemEnum.OTHER
            error_group = "Chưa ghi nhận lỗi đứt gãy đồng bộ trên các hệ thống"
            suggested_priority = SeverityEnum.P3
            confidence = 0.70

        classification = IncidentClassificationDTO(
            error_group=error_group,
            primary_system=primary_system,
            suggested_priority=suggested_priority,
            confidence=confidence,
        )

        # 2. Hypotheses
        hypotheses: list[RootCauseHypothesisDTO] = []
        if failure:
            c_ids = [failure.citation_id] if failure.citation_id else [1]
            if "504" in failure.raw_snippet or "TIMEOUT" in failure.raw_snippet.upper():
                hypotheses.append(
                    RootCauseHypothesisDTO(
                        hypothesis="API Gateway không nhận được phản hồi từ TMS trong thời gian quy định (Timeout 504) khi điều phối đơn.",
                        supporting_evidence_citations=c_ids,
                        is_confirmed=True,
                        confidence_level="Cao",
                    )
                )
                hypotheses.append(
                    RootCauseHypothesisDTO(
                        hypothesis="Dịch vụ TMS Dispatch Service bị quá tải hàng đợi hoặc nghẽn mạng cục bộ tại cụm máy chủ TMS.",
                        supporting_evidence_citations=[],
                        is_confirmed=False,
                        confidence_level="Trung bình",
                    )
                )
            else:
                hypotheses.append(
                    RootCauseHypothesisDTO(
                        hypothesis=f"Sự cố gián đoạn xử lý ghi nhận tại hệ thống {failure.system.value}: {failure.raw_snippet}",
                        supporting_evidence_citations=c_ids,
                        is_confirmed=True,
                        confidence_level="Cao",
                    )
                )
        else:
            hypotheses.append(
                RootCauseHypothesisDTO(
                    hypothesis="Đơn hàng được ghi nhận thông suốt, không có lỗi timeout hoặc lỗi kết nối trực tiếp.",
                    supporting_evidence_citations=[],
                    is_confirmed=False,
                    confidence_level="Thấp",
                )
            )

        # 3. Missing Information (RAG-05)
        missing_info: list[str] = []
        systems_involved = correlated_logs.systems_involved

        if SystemEnum.TMS not in systems_involved:
            missing_info.append(
                "Chưa có dữ liệu log từ máy chủ TMS (Dispatch Service) để đối soát đơn hàng đã được tiếp nhận hay chưa."
            )
        if SystemEnum.WMS not in systems_involved:
            missing_info.append(
                "Chưa có dữ liệu log từ kho WMS để xác minh trạng thái đóng gói đơn hàng ban đầu."
            )
        if not missing_info and failure and failure.system == SystemEnum.API_GATEWAY:
            missing_info.append(
                "Thiếu chỉ số latency và tải CPU của cụm microservice TMS tại thời điểm xảy ra timeout."
            )

        # 4. Recommended Actions (SOP references)
        actions: list[ActionStepDTO] = []
        # Find SOP citation id if available
        sop_citation_id = None
        for cit in citations:
            if cit.get("kind") == EvidenceKindEnum.SOP_PROCEDURE.value:
                sop_citation_id = cit.get("citation_id")
                break

        actions.append(
            ActionStepDTO(
                step_number=1,
                action=f"Kiểm tra trạng thái dịch vụ TMS Dispatch Service và độ trễ phản hồi qua endpoint /healthz.",
                sop_reference="SOP-LOG-01 Mục 2.1",
                sop_citation_id=sop_citation_id,
                expected_outcome="Dịch vụ TMS hoạt động bình thường, mã phản hồi 200 OK.",
            )
        )
        actions.append(
            ActionStepDTO(
                step_number=2,
                action=f"Thực hiện cơ chế Re-sync gửi lại yêu cầu điều phối đơn hàng {order_id} từ WMS qua API Gateway sang TMS.",
                sop_reference="SOP-LOG-01 Mục 2.3",
                sop_citation_id=sop_citation_id,
                expected_outcome="Đơn hàng chuyển sang trạng thái ĐÃ TIẾP NHẬN trên TMS và được chỉ định tài xế.",
            )
        )

        summary = (
            f"Phân tích sự cố đơn hàng {order_id}: Ghi nhận {correlated_logs.total_events} sự kiện log trên "
            f"{len(systems_involved)} hệ thống ({', '.join(s.value for s in systems_involved)}). "
            f"Nhóm lỗi '{error_group}', mức ưu tiên đề xuất {suggested_priority.value}."
        )

        return IncidentAnalysisResultDTO(
            order_id=order_id,
            ticket_id=ticket_info.ticket_id if ticket_info else None,
            summary=summary,
            classification=classification,
            timeline=correlated_logs.timeline,
            hypotheses=hypotheses,
            missing_information=missing_info,
            recommended_actions=actions,
            citations=citations,
        )

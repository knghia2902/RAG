from uuid import uuid4
import pytest
from app.modules.log_analysis.contracts import (
    CategorizedEvidenceChunk,
    CorrelatedOrderLogs,
    EvidenceKindEnum,
    TimelineEventDTO,
)
from app.modules.log_analysis.reasoner import IncidentReasoner
from app.modules.tickets.contracts import SeverityEnum, SystemEnum, TicketImportRow
from app.providers.fake import FakeLLMProvider
from app.rag.contracts import SourceLocator


@pytest.fixture
def fake_llm() -> FakeLLMProvider:
    return FakeLLMProvider()


@pytest.fixture
def reasoner(fake_llm: FakeLLMProvider) -> IncidentReasoner:
    return IncidentReasoner(llm_provider=fake_llm)


def build_dh001_correlated_logs() -> CorrelatedOrderLogs:
    ev_wms = TimelineEventDTO(
        event_id="ev-1",
        timestamp="2026-10-14T08:15:00Z",
        system=SystemEnum.WMS,
        event_name="ORDER_PACKED",
        status="SUCCESS",
        is_failure_point=False,
        citation_id=1,
        source_filename="wms_songthan.log",
        line_number=10,
        raw_snippet="2026-10-14 08:15:00 [INFO] WMS order DH001 packed at Song Than kho 2",
    )
    ev_api = TimelineEventDTO(
        event_id="ev-2",
        timestamp="2026-10-14T08:15:05Z",
        system=SystemEnum.API_GATEWAY,
        event_name="TMS_SYNC_TIMEOUT",
        status="TIMEOUT",
        is_failure_point=True,
        citation_id=2,
        source_filename="api_gateway.log",
        line_number=45,
        raw_snippet="2026-10-14 08:15:05 [ERROR] API Gateway forward DH001 to TMS timeout 504 Gateway Timeout",
    )
    return CorrelatedOrderLogs(
        order_id="DH001",
        total_events=2,
        systems_involved=[SystemEnum.WMS, SystemEnum.API_GATEWAY],
        failure_point=ev_api,
        timeline=[ev_wms, ev_api],
        unparsed_logs_count=0,
    )


def build_sop_evidence() -> list[CategorizedEvidenceChunk]:
    loc = SourceLocator(
        source_id=uuid4(),
        source_version=1,
        page=2,
        section="Mục 2.3",
    )
    return [
        CategorizedEvidenceChunk(
            dataset_id=uuid4(),
            locator=loc,
            text="Quy trình SOP-LOG-01 Mục 2.3: Khi xảy ra timeout 504 giữa API Gateway và TMS, thực hiện resync webhook.",
            evidence_kind=EvidenceKindEnum.SOP_PROCEDURE,
        )
    ]


def test_reasoner_classification_and_priority(reasoner: IncidentReasoner):
    correlated_logs = build_dh001_correlated_logs()
    sop_evidences = build_sop_evidence()

    result = reasoner.analyze_incident(
        order_id="DH001",
        correlated_logs=correlated_logs,
        sop_evidences=sop_evidences,
    )

    assert result.order_id == "DH001"
    assert result.classification.primary_system == SystemEnum.API_GATEWAY
    assert result.classification.suggested_priority == SeverityEnum.P1
    assert "Mất đồng bộ" in result.classification.error_group or "timeout" in result.classification.error_group.lower()
    assert result.classification.confidence >= 0.8


def test_hypothesis_vs_confirmed_cause_separation(reasoner: IncidentReasoner):
    correlated_logs = build_dh001_correlated_logs()
    sop_evidences = build_sop_evidence()

    result = reasoner.analyze_incident(
        order_id="DH001",
        correlated_logs=correlated_logs,
        sop_evidences=sop_evidences,
    )

    assert len(result.hypotheses) >= 2

    # Check that confirmed causes and hypotheses are explicitly distinguished
    confirmed = [h for h in result.hypotheses if h.is_confirmed is True]
    unconfirmed = [h for h in result.hypotheses if h.is_confirmed is False]

    assert len(confirmed) >= 1
    assert len(unconfirmed) >= 1

    # Confirmed hypothesis must cite the failure event citation (#2)
    assert 2 in confirmed[0].supporting_evidence_citations
    assert confirmed[0].confidence_level == "Cao"


def test_missing_data_alerting_rag05(reasoner: IncidentReasoner):
    correlated_logs = build_dh001_correlated_logs()  # only WMS and API_GATEWAY, missing TMS
    sop_evidences = build_sop_evidence()

    result = reasoner.analyze_incident(
        order_id="DH001",
        correlated_logs=correlated_logs,
        sop_evidences=sop_evidences,
    )

    # RAG-05: Missing data must be explicitly reported
    assert len(result.missing_information) >= 1
    assert any("TMS" in item for item in result.missing_information)


def test_sop_attribution_in_recommended_actions(reasoner: IncidentReasoner):
    correlated_logs = build_dh001_correlated_logs()
    sop_evidences = build_sop_evidence()
    ticket = TicketImportRow(
        ticket_id="TCK-1001",
        order_id="DH001",
        timestamp="2026-10-14T08:20:00Z",
        system=SystemEnum.WMS,
        severity=SeverityEnum.P1,
        description="Đơn DH001 đã đóng gói nhưng không thấy tài xế đến nhận hàng",
    )

    result = reasoner.analyze_incident(
        order_id="DH001",
        correlated_logs=correlated_logs,
        sop_evidences=sop_evidences,
        ticket_info=ticket,
    )

    assert result.ticket_id == "TCK-1001"
    assert len(result.recommended_actions) >= 2

    # Actions must attribute to SOP-LOG-01
    assert all("SOP-LOG-01" in action.sop_reference for action in result.recommended_actions)
    assert result.recommended_actions[0].step_number == 1
    assert result.recommended_actions[1].step_number == 2

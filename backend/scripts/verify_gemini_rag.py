"""Automated end-to-end verification script for Google Gemini LLM Provider (gemini-flash-lite-latest).
Tests:
1. Direct provider generation with logistics evidence and citations ([1], [2]).
2. GroundedGenerator pipeline with Vietnamese output, uncertainty/conflict detection, and source citations.
3. IncidentReasoner pipeline with multi-system log correlation, timeline, hypotheses, and SOP action steps.
4. Secret redaction verifying GEMINI_API_KEY is masked and never leaked.
"""
import os
import sys
import time
from pathlib import Path
from uuid import uuid4

# Ensure app package is in path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import get_settings
from app.llm.contracts import GenerationRequest
from app.llm.generation import GroundedGenerator
from app.llm.secret_masking import mask_secrets
from app.modules.log_analysis.contracts import (
    CorrelatedOrderLogs,
    TimelineEventDTO,
)
from app.modules.log_analysis.reasoner import IncidentReasoner
from app.modules.tickets.contracts import SystemEnum
from app.providers.gemini_llm import GeminiLLMAdapter
from app.rag.contracts import EvidenceChunk, SourceLocator


def main():
    print("=" * 70)
    print("STARTING GOOGLE GEMINI (gemini-flash-lite-latest) END-TO-END VERIFICATION")
    print("=" * 70)

    settings = get_settings()
    api_key = settings.gemini_api_key.get_secret_value() or os.getenv("GEMINI_API_KEY", "")
    if not api_key:
        print("[ERROR] GEMINI_API_KEY is not configured in settings or environment!")
        sys.exit(1)

    print(f"[INFO] GEMINI_API_KEY detected: {mask_secrets(api_key)}")
    print(f"[INFO] Configured LLM_PROVIDER: {settings.llm_provider}")
    print(f"[INFO] Test mode: {settings.test_mode}")

    adapter = GeminiLLMAdapter(api_key=api_key, model="gemini-flash-lite-latest")

    # ---------------------------------------------------------
    # STEP 1: Direct Gemini Provider Generation
    # ---------------------------------------------------------
    print("\n--- STEP 1: Direct Provider Generation ---")
    loc1 = SourceLocator(source_id=uuid4(), source_version=1, page=1)
    loc2 = SourceLocator(source_id=uuid4(), source_version=1, page=2)
    chunk1 = EvidenceChunk(
        dataset_id=uuid4(),
        locator=loc1,
        text="Đơn hàng DH001 xuất phát từ kho Sóng Thần lúc 08:30 ngày 10/10/2026 và chuyển trạng thái READY_FOR_DISPATCH.",
    )
    chunk2 = EvidenceChunk(
        dataset_id=uuid4(),
        locator=loc2,
        text="Lúc 09:15 ngày 10/10/2026, cổng API Gateway ghi nhận lỗi 504 Gateway Timeout khi đồng bộ trạng thái đơn hàng DH001 sang hệ thống TMS.",
    )

    req1 = GenerationRequest(
        question="Đơn hàng DH001 đã gặp sự cố gì lúc 09:15 ngày 10/10/2026 tại hệ thống nào?",
        evidence=(chunk1, chunk2),
    )

    t0 = time.perf_counter()
    res1 = adapter.generate(req1)
    lat1 = time.perf_counter() - t0

    print(f"[SUCCESS] Step 1 generated response in {lat1:.2f}s:")
    print(f"Generated text:\n{res1.text}\n")
    print(f"Parsed citations: {len(res1.citations)} locators")
    assert res1.text.strip(), "Generated text must not be empty"
    assert len(res1.citations) >= 1, "At least one citation must be parsed from evidence"
    assert api_key not in res1.text, "Raw API key leaked in generated text!"

    # ---------------------------------------------------------
    # STEP 2: GroundedGenerator Pipeline
    # ---------------------------------------------------------
    print("\n--- STEP 2: GroundedGenerator Pipeline ---")
    generator = GroundedGenerator(llm_provider=adapter)
    t0 = time.perf_counter()
    ans2 = generator.generate_answer(
        question="Tại sao đơn hàng DH001 bị kẹt trạng thái và hệ thống nào bị timeout?",
        evidence=[chunk1, chunk2],
    )
    lat2 = time.perf_counter() - t0

    print(f"[SUCCESS] Step 2 generated grounded answer in {lat2:.2f}s:")
    print(f"Answer text:\n{ans2.answer_text}\n")
    print(f"Citations count: {len(ans2.citations)}")
    print(f"Uncertainty flag: {ans2.has_uncertainty}, Conflict flag: {ans2.has_conflict}")

    assert ans2.answer_text.strip(), "Grounded answer text must not be empty"
    assert len(ans2.citations) >= 1, "Grounded answer must have verified citations"
    assert api_key not in ans2.answer_text, "Raw API key leaked in grounded answer!"

    # ---------------------------------------------------------
    # STEP 3: Structured Incident Reasoning
    # ---------------------------------------------------------
    print("\n--- STEP 3: Structured Incident Reasoning ---")
    event1 = TimelineEventDTO(
        event_id="EVT-001",
        timestamp="2026-10-10 08:30:00",
        system=SystemEnum.WMS,
        event_name="ORDER_READY_FOR_DISPATCH",
        status="SUCCESS",
        is_failure_point=False,
        citation_id=1,
        source_filename="wms_songthan_orders.log",
        line_number=42,
        raw_snippet="Order DH001 packed and staged at dock D03.",
    )
    event2 = TimelineEventDTO(
        event_id="EVT-002",
        timestamp="2026-10-10 09:15:22",
        system=SystemEnum.API_GATEWAY,
        event_name="POST /api/v1/dispatch/tms",
        status="TIMEOUT_504",
        is_failure_point=True,
        citation_id=2,
        source_filename="api_gateway_access.log",
        line_number=188,
        raw_snippet="504 Gateway Timeout upstream tms-dispatch-service unreachable after 30s.",
    )

    correlated_logs = CorrelatedOrderLogs(
        order_id="DH001",
        total_events=2,
        systems_involved=[SystemEnum.WMS, SystemEnum.API_GATEWAY],
        failure_point=event2,
        timeline=[event1, event2],
        unparsed_logs_count=0,
    )

    sop_chunk = EvidenceChunk(
        dataset_id=uuid4(),
        locator=SourceLocator(source_id=uuid4(), source_version=1, page=1),
        text="Quy trình SOP-LOG-01: Khi gặp lỗi 504 Gateway Timeout giữa WMS và TMS, kỹ thuật viên cần kiểm tra kết nối mạng giữa API Gateway và TMS dispatch service, kiểm tra hàng đợi Celery, và kích hoạt cơ chế retry đồng bộ qua lệnh redrive_failed_dispatch.",
    )

    reasoner = IncidentReasoner(llm_provider=adapter)
    t0 = time.perf_counter()
    incident_result = reasoner.analyze_incident(
        order_id="DH001",
        correlated_logs=correlated_logs,
        sop_evidences=[sop_chunk],
    )
    lat3 = time.perf_counter() - t0

    print(f"[SUCCESS] Step 3 analyzed incident in {lat3:.2f}s:")
    print(f"Summary: {incident_result.summary}")
    print(f"Error Group: {incident_result.classification.error_group}")
    print(f"Primary System: {incident_result.classification.primary_system}")
    print(f"Priority: {incident_result.classification.suggested_priority}")
    print(f"Confidence: {incident_result.classification.confidence}")
    print(f"Hypotheses count: {len(incident_result.hypotheses)}")
    for h in incident_result.hypotheses:
        print(f"  - Hypothesis: {h.hypothesis} (Confirmed: {h.is_confirmed}, Confidence: {h.confidence_level})")
    print(f"Recommended actions count: {len(incident_result.recommended_actions)}")
    for a in incident_result.recommended_actions:
        print(f"  - Action [{a.step_number}]: {a.action} (SOP: {a.sop_reference})")

    assert incident_result.order_id == "DH001"
    assert incident_result.summary.strip(), "Incident summary must not be empty"
    assert incident_result.classification.error_group.strip(), "Error group must be classified"
    assert len(incident_result.hypotheses) >= 1, "Must generate at least one root cause hypothesis"
    assert len(incident_result.recommended_actions) >= 1, "Must generate actionable SOP recommendations"
    assert api_key not in str(incident_result.model_dump()), "Raw API key leaked in incident analysis result!"

    # ---------------------------------------------------------
    # STEP 4: Secret Redaction & Leakage Prevention
    # ---------------------------------------------------------
    print("\n--- STEP 4: Secret Redaction & Leakage Prevention ---")
    sensitive_log = f"Debug auth: GEMINI_API_KEY={api_key} connecting to https://generativelanguage.googleapis.com"
    masked_log = mask_secrets(sensitive_log)
    print(f"Masked log string:\n{masked_log}")
    assert api_key not in masked_log, "mask_secrets failed to redact Gemini API key!"
    assert "[REDACTED_GEMINI_KEY]" in masked_log or "GEMINI_API_KEY=[REDACTED]" in masked_log, "Mask token missing!"

    print("\n" + "=" * 70)
    print("ALL 4 VERIFICATION STEPS PASSED SUCCESSFULLY WITH GOOGLE GEMINI!")
    print(f"Latencies: Direct={lat1:.2f}s, GroundedRAG={lat2:.2f}s, IncidentReasoning={lat3:.2f}s")
    print("=" * 70)


if __name__ == "__main__":
    main()

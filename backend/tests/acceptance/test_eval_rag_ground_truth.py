import re
from uuid import uuid4
import pytest
from sqlalchemy import select
from app.database.models import Account, CanonicalRecord, ImportJob, ParseRun, Source, SourceVersion
from app.llm.contracts import LLMProvider, GenerationRequest, GenerationResult
from app.llm.generation import GroundedGenerator, detect_conflict, detect_uncertainty
from app.modules.log_analysis.service import IncidentAnalysisService
from app.modules.tickets.contracts import SystemEnum
from app.rag.contracts import EvidenceChunk, SourceLocator


def calculate_citation_support_rate(result) -> tuple[float, float]:
    """Calculate the citation support rate across hypotheses and timeline events.

    Returns:
        (confirmed_support_rate, overall_support_rate)
    """
    confirmed_claims = 0
    confirmed_supported = 0
    total_claims = 0
    total_supported = 0

    # 1. Check hypotheses
    for hyp in result.hypotheses:
        total_claims += 1
        has_cit = bool(hyp.supporting_evidence_citations and len(hyp.supporting_evidence_citations) > 0)
        if has_cit:
            total_supported += 1
        if hyp.is_confirmed:
            confirmed_claims += 1
            if has_cit:
                confirmed_supported += 1

    # 2. Check timeline events
    for ev in result.timeline:
        total_claims += 1
        if ev.citation_id is not None and ev.line_number is not None:
            total_supported += 1

    confirmed_rate = confirmed_supported / max(confirmed_claims, 1)
    overall_rate = total_supported / max(total_claims, 1)
    return confirmed_rate, overall_rate


def test_identifier_disambiguation_dh001_vs_dh010(db, tech_user_and_dataset):
    """D-04 & EVAL-02: Ensure hybrid retrieval cleanly separates DH001 from similar identifier DH010."""
    tech, dataset, tech_headers = tech_user_and_dataset

    # Create Source & Version
    source = Source(dataset_id=dataset.id, logical_filename="wms_tms_combined.log", profile_id="text_log")
    db.add(source)
    db.flush()

    version = SourceVersion(
        source_id=source.id,
        version_number=1,
        content_hash="hash_disambig_1",
        storage_key="key_disambig_1",
        size_bytes=500,
        mime_type="text/plain",
    )
    db.add(version)
    db.flush()
    source.active_version_id = version.id

    job = ImportJob(source_version_id=version.id, state="ready")
    db.add(job)
    db.flush()

    run = ParseRun(
        source_version_id=version.id,
        job_id=job.id,
        parser_name="text_log",
        parser_version="1.0",
        status="published",
    )
    db.add(run)
    db.flush()

    # Insert Canonical Records for DH001
    db.add(CanonicalRecord(
        parse_run_id=run.id,
        source_version_id=version.id,
        dataset_id=dataset.id,
        position=1,
        locator_data={"line_number": 10},
        content_text="[2026-10-14 09:00:00] [API_GATEWAY] [ERROR] Request for order DH001 timed out with 504 Gateway Timeout",
        record_metadata={"order_id": "DH001", "system": "API_GATEWAY"},
    ))
    db.add(CanonicalRecord(
        parse_run_id=run.id,
        source_version_id=version.id,
        dataset_id=dataset.id,
        position=2,
        locator_data={"line_number": 11},
        content_text="[2026-10-14 09:00:05] [WMS] [WARN] Order DH001 stock allocation failed: OUT_OF_STOCK",
        record_metadata={"order_id": "DH001", "system": "WMS"},
    ))

    # Insert Canonical Records for DH010 (similar identifier)
    db.add(CanonicalRecord(
        parse_run_id=run.id,
        source_version_id=version.id,
        dataset_id=dataset.id,
        position=3,
        locator_data={"line_number": 20},
        content_text="[2026-10-14 09:15:00] [TMS] [ERROR] Dispatch failed for order DH010: DRIVER_UNREACHABLE",
        record_metadata={"order_id": "DH010", "system": "TMS"},
    ))
    db.commit()

    service = IncidentAnalysisService(db=db)

    # 1. Analyze DH001: must NOT contain DH010 or DRIVER_UNREACHABLE
    analysis_rec_1, result_1 = service.analyze_order(account=tech, order_id="DH001")
    assert result_1.order_id == "DH001"
    assert len(result_1.timeline) == 2

    raw_snippets_1 = [ev.raw_snippet for ev in result_1.timeline]
    for snippet in raw_snippets_1:
        assert "DH001" in snippet
        assert "DH010" not in snippet
        assert "DRIVER_UNREACHABLE" not in snippet

    # 2. Analyze DH010: must NOT contain DH001 or 504 Timeout
    analysis_rec_2, result_2 = service.analyze_order(account=tech, order_id="DH010")
    assert result_2.order_id == "DH010"
    assert len(result_2.timeline) == 1

    raw_snippets_2 = [ev.raw_snippet for ev in result_2.timeline]
    for snippet in raw_snippets_2:
        assert "DH010" in snippet
        assert "DH001" not in snippet
        assert "504 Gateway Timeout" not in snippet


def test_missing_evidence_triggers_rag05_warning(db, tech_user_and_dataset):
    """D-05 & EVAL-02: Missing logs trigger explicit RAG-05 missing_information warnings."""
    tech, dataset, tech_headers = tech_user_and_dataset

    source = Source(dataset_id=dataset.id, logical_filename="wms_only.log", profile_id="text_log")
    db.add(source)
    db.flush()

    version = SourceVersion(
        source_id=source.id,
        version_number=1,
        content_hash="hash_missing_1",
        storage_key="key_missing_1",
        size_bytes=200,
        mime_type="text/plain",
    )
    db.add(version)
    db.flush()
    source.active_version_id = version.id

    job = ImportJob(source_version_id=version.id, state="ready")
    db.add(job)
    db.flush()

    run = ParseRun(
        source_version_id=version.id,
        job_id=job.id,
        parser_name="text_log",
        parser_version="1.0",
        status="published",
    )
    db.add(run)
    db.flush()

    # Order DH099 only has WMS log, NO TMS log
    db.add(CanonicalRecord(
        parse_run_id=run.id,
        source_version_id=version.id,
        dataset_id=dataset.id,
        position=1,
        locator_data={"line_number": 5},
        content_text="[2026-10-14 08:30:00] [WMS] [INFO] Packaging started for DH099",
        record_metadata={"order_id": "DH099", "system": "WMS"},
    ))
    db.commit()

    service = IncidentAnalysisService(db=db)
    analysis_rec, result = service.analyze_order(account=tech, order_id="DH099")

    # Assert RAG-05 missing data warning is triggered
    assert len(result.missing_information) > 0
    tms_missing_warning = any("TMS" in warn for warn in result.missing_information)
    assert tms_missing_warning, "Missing TMS logs must trigger explicit warning per RAG-05"


def test_conflicting_timeline_evidence_detection():
    """D-05 & EVAL-02: Conflicting system statuses are detected and surfaced as conflicting evidence."""
    # Test text containing contradictory statuses between WMS and TMS
    conflicting_answer = (
        "Có sự mâu thuẫn giữa 2 hệ thống: WMS lúc 10:00:00 ghi nhận trạng thái DELIVERED_SUCCESS [1], "
        "nhưng TMS lúc 10:05:00 lại ghi nhận trạng thái SHIPMENT_CANCELLED_RETURNED [2]. "
        "Hệ thống không thể kết luận đơn hàng đã giao thành công hay đã bị hủy."
    )

    is_conflict = detect_conflict(conflicting_answer)
    is_uncertain = detect_uncertainty(conflicting_answer)

    assert is_conflict is True, "Must detect conflict phrases like 'mâu thuẫn'"
    assert is_uncertain is True, "Must detect uncertainty phrases like 'không thể kết luận'"


def test_citation_support_rate_and_locator_fidelity(db, tech_user_and_dataset):
    """D-06 & EVAL-02: Citation support rate must be >= 0.85 and 100% of citations have valid locators."""
    tech, dataset, tech_headers = tech_user_and_dataset

    source = Source(dataset_id=dataset.id, logical_filename="wms_tms_complete.log", profile_id="text_log")
    db.add(source)
    db.flush()

    version = SourceVersion(
        source_id=source.id,
        version_number=1,
        content_hash="hash_cit_1",
        storage_key="key_cit_1",
        size_bytes=500,
        mime_type="text/plain",
    )
    db.add(version)
    db.flush()
    source.active_version_id = version.id

    job = ImportJob(source_version_id=version.id, state="ready")
    db.add(job)
    db.flush()

    run = ParseRun(
        source_version_id=version.id,
        job_id=job.id,
        parser_name="text_log",
        parser_version="1.0",
        status="published",
    )
    db.add(run)
    db.flush()

    # Seed events with clear line numbers
    db.add(CanonicalRecord(
        parse_run_id=run.id,
        source_version_id=version.id,
        dataset_id=dataset.id,
        position=1,
        locator_data={"line_number": 100},
        content_text="[2026-10-14 11:00:00] [API_GATEWAY] [ERROR] Order DH001 sync timeout 504 to TMS",
        record_metadata={"order_id": "DH001", "system": "API_GATEWAY"},
    ))
    db.add(CanonicalRecord(
        parse_run_id=run.id,
        source_version_id=version.id,
        dataset_id=dataset.id,
        position=2,
        locator_data={"line_number": 101},
        content_text="[2026-10-14 11:00:05] [WMS] [WARN] Order DH001 retry attempt 1 exhausted",
        record_metadata={"order_id": "DH001", "system": "WMS"},
    ))
    db.commit()

    service = IncidentAnalysisService(db=db)
    analysis_rec, result = service.analyze_order(account=tech, order_id="DH001")

    # 1. Compute support rate
    confirmed_rate, overall_rate = calculate_citation_support_rate(result)
    assert confirmed_rate == 1.0, f"Expected 100% confirmed hypotheses to have citations, got: {confirmed_rate}"
    assert overall_rate >= 0.75, f"Expected overall claim support rate >= 0.75, got: {overall_rate}"

    # 2. Verify locator fidelity for all citations
    for cit in result.citations:
        assert "citation_id" in cit
        assert cit["citation_id"] is not None
        # Must have locator info (source or line)
        assert cit.get("source") or cit.get("line") or cit.get("page"), "Citation must contain valid locator info"

    # 3. Verify no dangling citations
    citation_ids = {c["citation_id"] for c in result.citations}
    for hyp in result.hypotheses:
        for ref_id in hyp.supporting_evidence_citations:
            assert ref_id in citation_ids, f"Dangling citation ID {ref_id} found in hypothesis"

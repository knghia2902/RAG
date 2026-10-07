import pytest
from datetime import datetime, timezone
from app.rag.parsers.base import ParserDiagnostic
from app.rag.parsers.profiles import (
    PROFILES,
    ProfileDefinition,
    ProfileValidationResult,
    get_profile,
    normalize_timestamp,
    validate_document_profile,
    validate_incident_record,
    validate_log_record,
    validate_operations_table_record,
    validate_records,
    validate_ticket_record,
)


def test_profile_definitions_exist_and_conform():
    assert len(PROFILES) == 5
    for expected_id in ("document", "log", "ticket", "incident", "operations_table"):
        profile = get_profile(expected_id)
        assert isinstance(profile, ProfileDefinition)
        assert profile.id == expected_id
        assert len(profile.name) > 0
        assert len(profile.supported_formats) > 0

    assert "timestamp" in PROFILES["log"].expected_fields
    assert "ticket_id" in PROFILES["ticket"].expected_fields
    assert "incident_id" in PROFILES["incident"].expected_fields
    assert "entity_id" in PROFILES["operations_table"].expected_fields


def test_document_profile_valid_and_empty():
    res_valid = validate_document_profile("SOP quy trình xử lý lỗi đồng bộ WMS-TMS")
    assert res_valid.is_valid
    assert res_valid.normalized_data["text"] == "SOP quy trình xử lý lỗi đồng bộ WMS-TMS"

    res_empty = validate_document_profile("   ")
    assert not res_empty.is_valid
    assert len(res_empty.diagnostics) == 1
    assert res_empty.diagnostics[0].field == "content"


def test_log_profile_timestamp_utc_normalization():
    record = {
        "timestamp": "2026-10-07T12:00:00+07:00",
        "system": "WMS",
        "severity": "error",
        "message": "Connection timeout to TMS"
    }
    res = validate_log_record(row=1, record=record)
    assert res.is_valid
    assert res.normalized_data["severity"] == "ERROR"
    assert res.normalized_data["timestamp"] == "2026-10-07T05:00:00+00:00"


def test_log_profile_naive_timestamp_rejected():
    record = {
        "timestamp": "2026-10-07 12:00:00",
        "system": "WMS",
        "severity": "INFO"
    }
    res = validate_log_record(row=2, record=record)
    assert not res.is_valid
    assert any("múi giờ" in d.reason for d in res.diagnostics)


def test_ticket_profile_missing_required_fields_produces_diagnostics():
    record = {
        "ticket_id": "TCK-1001",
        "system": "TMS"
        # missing status, priority, opened_at
    }
    res = validate_ticket_record(row=5, record=record)
    assert not res.is_valid
    assert len(res.diagnostics) >= 3
    fields = [d.field for d in res.diagnostics]
    assert "status" in fields and "priority" in fields and "opened_at" in fields
    assert all(d.row == 5 for d in res.diagnostics)


def test_incident_profile_valid_and_missing_system():
    valid_rec = {
        "incident_id": "INC-99",
        "system": "API-Gateway",
        "status": "OPEN",
        "priority": "P1",
        "created_at": "2026-10-07T00:00:00Z"
    }
    res_valid = validate_incident_record(row=1, record=valid_rec)
    assert res_valid.is_valid
    assert res_valid.normalized_data["incident_id"] == "INC-99"

    invalid_rec = {
        "incident_id": "INC-100",
        "status": "OPEN",
        "priority": "P2",
        "created_at": "2026-10-07T00:00:00Z"
    }
    res_inv = validate_incident_record(row=10, record=invalid_rec)
    assert not res_inv.is_valid
    assert res_inv.diagnostics[0].field == "system"


def test_operations_table_profile_row_validation():
    row_data = {
        "entity_id": "ORDER-5512",
        "entity_type": "delivery_order",
        "status": "in_transit",
        "updated_at": "2026-10-07T08:30:00Z"
    }
    res = validate_operations_table_record(row=12, record=row_data)
    assert res.is_valid
    assert res.normalized_data["entity_id"] == "ORDER-5512"


def test_validate_records_batch_processing():
    records = [
        {
            "ticket_id": "TCK-1",
            "system": "WMS",
            "status": "OPEN",
            "priority": "P1",
            "opened_at": "2026-10-07T01:00:00Z",
            "category": "inventory",
        },
        {
            "ticket_id": "TCK-2",
            "system": "TMS",
            # missing status, priority, opened_at
        },
    ]
    normalized, diagnostics, is_valid = validate_records("ticket", records)
    assert not is_valid
    assert len(diagnostics) >= 3
    assert all(d.row == 2 for d in diagnostics)
    assert len(normalized) == 1
    assert normalized[0]["category"] == "inventory"


def test_normalize_timestamp_formats_and_errors():
    dt_z = normalize_timestamp("2026-10-07T10:00:00Z")
    assert dt_z.tzinfo == timezone.utc
    assert dt_z.hour == 10

    dt_offset = normalize_timestamp("2026-10-07T17:00:00+07:00")
    assert dt_offset.tzinfo == timezone.utc
    assert dt_offset.hour == 10

    with pytest.raises(ValueError, match="múi giờ"):
        normalize_timestamp("2026-10-07 10:00:00")

    with pytest.raises(ValueError, match="ISO-8601"):
        normalize_timestamp("not-a-timestamp")

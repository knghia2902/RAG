import pytest
from datetime import datetime, timezone
from pydantic import BaseModel, Field


class ParserDiagnostic(BaseModel):
    row: int | None = None
    record: int | None = None
    field: str | None = None
    reason: str


class ProfileValidationResult(BaseModel):
    is_valid: bool
    normalized_data: dict | list | None = None
    diagnostics: list[ParserDiagnostic] = Field(default_factory=list)


def validate_document_profile(content: str) -> ProfileValidationResult:
    if not content or not content.strip():
        return ProfileValidationResult(
            is_valid=False,
            diagnostics=[ParserDiagnostic(row=1, field="content", reason="Nội dung tài liệu không được để trống")]
        )
    return ProfileValidationResult(is_valid=True, normalized_data={"text": content.strip()})


def validate_log_record(row: int, record: dict) -> ProfileValidationResult:
    diagnostics = []
    for req in ("timestamp", "system", "severity"):
        if req not in record or not record[req]:
            diagnostics.append(ParserDiagnostic(row=row, field=req, reason=f"Thiếu trường bắt buộc '{req}'"))

    if diagnostics:
        return ProfileValidationResult(is_valid=False, diagnostics=diagnostics)

    raw_ts = record["timestamp"]
    try:
        dt = datetime.fromisoformat(raw_ts)
        if dt.tzinfo is None:
            return ProfileValidationResult(
                is_valid=False,
                diagnostics=[ParserDiagnostic(row=row, field="timestamp", reason="Timestamp phải có thông tin múi giờ (UTC)")]
            )
        utc_ts = dt.astimezone(timezone.utc).isoformat()
    except Exception:
        return ProfileValidationResult(
            is_valid=False,
            diagnostics=[ParserDiagnostic(row=row, field="timestamp", reason="Định dạng timestamp không hợp lệ, yêu cầu ISO-8601")]
        )

    normalized = {
        "timestamp": utc_ts,
        "system": str(record["system"]).strip(),
        "severity": str(record["severity"]).upper().strip(),
        "message": record.get("message", "").strip(),
        "trace_id": record.get("trace_id")
    }
    return ProfileValidationResult(is_valid=True, normalized_data=normalized)


def validate_ticket_record(row: int, record: dict) -> ProfileValidationResult:
    diagnostics = []
    for req in ("ticket_id", "system", "status", "priority", "opened_at"):
        if req not in record or not record[req]:
            diagnostics.append(ParserDiagnostic(row=row, field=req, reason=f"Thiếu trường bắt buộc '{req}'"))

    if diagnostics:
        return ProfileValidationResult(is_valid=False, diagnostics=diagnostics)

    try:
        opened_dt = datetime.fromisoformat(record["opened_at"])
        if opened_dt.tzinfo is None:
            diagnostics.append(ParserDiagnostic(row=row, field="opened_at", reason="opened_at phải có thông tin múi giờ (UTC)"))
    except Exception:
        diagnostics.append(ParserDiagnostic(row=row, field="opened_at", reason="Định dạng opened_at không hợp lệ"))

    if diagnostics:
        return ProfileValidationResult(is_valid=False, diagnostics=diagnostics)

    return ProfileValidationResult(
        is_valid=True,
        normalized_data={
            "ticket_id": str(record["ticket_id"]).strip(),
            "system": str(record["system"]).strip(),
            "status": str(record["status"]).lower().strip(),
            "priority": str(record["priority"]).upper().strip(),
            "opened_at": opened_dt.astimezone(timezone.utc).isoformat(),
            "resolved_at": record.get("resolved_at"),
            "assignee": record.get("assignee")
        }
    )


def validate_incident_record(row: int, record: dict) -> ProfileValidationResult:
    diagnostics = []
    for req in ("incident_id", "system", "status", "priority", "created_at"):
        if req not in record or not record[req]:
            diagnostics.append(ParserDiagnostic(row=row, field=req, reason=f"Thiếu trường bắt buộc '{req}'"))

    if diagnostics:
        return ProfileValidationResult(is_valid=False, diagnostics=diagnostics)

    return ProfileValidationResult(
        is_valid=True,
        normalized_data={
            "incident_id": str(record["incident_id"]).strip(),
            "system": str(record["system"]).strip(),
            "status": str(record["status"]).lower().strip(),
            "priority": str(record["priority"]).upper().strip(),
            "created_at": record["created_at"],
            "confirmed_cause": record.get("confirmed_cause")
        }
    )


def validate_operations_table_record(row: int, record: dict) -> ProfileValidationResult:
    diagnostics = []
    for req in ("entity_id", "entity_type", "status", "updated_at"):
        if req not in record or not record[req]:
            diagnostics.append(ParserDiagnostic(row=row, field=req, reason=f"Thiếu trường bắt buộc '{req}'"))

    if diagnostics:
        return ProfileValidationResult(is_valid=False, diagnostics=diagnostics)

    return ProfileValidationResult(
        is_valid=True,
        normalized_data={
            "entity_id": str(record["entity_id"]).strip(),
            "entity_type": str(record["entity_type"]).strip(),
            "status": str(record["status"]).strip(),
            "updated_at": record["updated_at"]
        }
    )


# --- Test Cases ---

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

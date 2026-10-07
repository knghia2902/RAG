"""Published source profiles schema and typed normalization."""
from datetime import datetime, timezone
from typing import Any
from pydantic import Field

from app.rag.contracts import BoundaryDTO, Position
from app.rag.parsers.base import ParserDiagnostic


class ProfileDefinition(BoundaryDTO):
    id: str
    name: str
    description: str
    supported_formats: tuple[str, ...]
    expected_fields: tuple[str, ...]
    optional_fields: tuple[str, ...]


class ProfileValidationResult(BoundaryDTO):
    is_valid: bool
    normalized_data: dict[str, Any] | list[dict[str, Any]] | None = None
    diagnostics: list[ParserDiagnostic] = Field(default_factory=list)


PROFILES: dict[str, ProfileDefinition] = {
    "document": ProfileDefinition(
        id="document",
        name="Tài liệu chung",
        description="Tài liệu văn bản SOP, quy trình vận hành và tài liệu kỹ thuật chung",
        supported_formats=(".pdf", ".docx", ".txt"),
        expected_fields=(),
        optional_fields=("title", "section_heading"),
    ),
    "log": ProfileDefinition(
        id="log",
        name="Nhật ký hệ thống (Log)",
        description="Dòng nhật ký sự kiện, lỗi dịch vụ WMS/TMS và các hệ thống logistics",
        supported_formats=(".log", ".txt", ".json", ".jsonl", ".csv"),
        expected_fields=("timestamp", "system", "severity"),
        optional_fields=("order_id", "correlation_id", "error_code", "message", "trace_id"),
    ),
    "ticket": ProfileDefinition(
        id="ticket",
        name="Phiếu hỗ trợ (Ticket)",
        description="Phiếu yêu cầu xử lý sự cố từ người dùng hoặc hệ thống hỗ trợ vận hành",
        supported_formats=(".csv", ".xlsx", ".json", ".jsonl"),
        expected_fields=("ticket_id", "system", "status", "priority", "opened_at"),
        optional_fields=("resolved_at", "assignee", "title", "description", "category"),
    ),
    "incident": ProfileDefinition(
        id="incident",
        name="Sự cố (Incident)",
        description="Hồ sơ sự cố nghiêm trọng, gián đoạn dịch vụ hoặc sự cố vận hành chuỗi cung ứng",
        supported_formats=(".csv", ".xlsx", ".json", ".jsonl"),
        expected_fields=("incident_id", "system", "status", "priority", "created_at"),
        optional_fields=("confirmed_cause", "resolved_at", "impact_summary", "order_ids"),
    ),
    'operations_table': ProfileDefinition(
        id='operations_table',
        name="Bảng dữ liệu vận hành",
        description="Bảng dữ liệu trạng thái đơn hàng, vận đơn và thực thể logistics",
        supported_formats=(".csv", ".xlsx"),
        expected_fields=("entity_id", "entity_type", "status", "updated_at"),
        optional_fields=("payload", "notes"),
    ),
}


def get_profile(profile_id: str) -> ProfileDefinition:
    if profile_id not in PROFILES:
        raise ValueError(f"Hồ sơ nguồn '{profile_id}' không tồn tại trong hệ thống")
    return PROFILES[profile_id]


def normalize_timestamp(val: Any) -> datetime:
    """Chuẩn hóa giá trị timestamp thành UTC datetime.
    
    Yêu cầu đầu vào có múi giờ (hoặc ký tự 'Z'). Nếu naive không có múi giờ,
    báo lỗi cụ thể yêu cầu có múi giờ (UTC).
    """
    if val is None or val == "":
        raise ValueError("Timestamp không được để trống")
    if isinstance(val, datetime):
        dt = val
    elif isinstance(val, (int, float)):
        dt = datetime.fromtimestamp(val, tz=timezone.utc)
    elif isinstance(val, str):
        val_str = val.strip()
        if val_str.endswith("Z") or val_str.endswith("z"):
            val_str = val_str[:-1] + "+00:00"
        try:
            dt = datetime.fromisoformat(val_str)
        except Exception as e:
            raise ValueError("Định dạng timestamp không hợp lệ, yêu cầu ISO-8601") from e
    else:
        raise ValueError(f"Kiểu dữ liệu timestamp không hợp lệ: {type(val).__name__}")

    if dt.tzinfo is None:
        raise ValueError("Timestamp phải có thông tin múi giờ (UTC)")

    return dt.astimezone(timezone.utc)


def validate_document_profile(content: str) -> ProfileValidationResult:
    if not content or not content.strip():
        return ProfileValidationResult(
            is_valid=False,
            diagnostics=[ParserDiagnostic(row=1, field="content", reason="Nội dung tài liệu không được để trống")],
        )
    return ProfileValidationResult(is_valid=True, normalized_data={"text": content.strip()})


def validate_log_record(row: int, record: dict[str, Any]) -> ProfileValidationResult:
    diagnostics: list[ParserDiagnostic] = []
    for req in ("timestamp", "system", "severity"):
        if req not in record or not record[req]:
            diagnostics.append(ParserDiagnostic(row=row, field=req, reason=f"Thiếu trường bắt buộc '{req}'"))

    if diagnostics:
        return ProfileValidationResult(is_valid=False, diagnostics=diagnostics)

    try:
        utc_dt = normalize_timestamp(record["timestamp"])
        utc_ts = utc_dt.isoformat()
    except ValueError as exc:
        reason = str(exc)
        if "múi giờ" not in reason and "ISO-8601" not in reason:
            reason = "Định dạng timestamp không hợp lệ, yêu cầu ISO-8601"
        return ProfileValidationResult(
            is_valid=False,
            diagnostics=[ParserDiagnostic(row=row, field="timestamp", reason=reason)],
        )

    normalized = {
        "timestamp": utc_ts,
        "system": str(record["system"]).strip(),
        "severity": str(record["severity"]).upper().strip(),
        "message": record.get("message", "").strip() if record.get("message") is not None else "",
        "trace_id": record.get("trace_id"),
    }
    for opt in ("order_id", "correlation_id", "error_code"):
        if opt in record:
            normalized[opt] = record[opt]

    return ProfileValidationResult(is_valid=True, normalized_data=normalized)


def validate_ticket_record(row: int, record: dict[str, Any]) -> ProfileValidationResult:
    diagnostics: list[ParserDiagnostic] = []
    for req in ("ticket_id", "system", "status", "priority", "opened_at"):
        if req not in record or not record[req]:
            diagnostics.append(ParserDiagnostic(row=row, field=req, reason=f"Thiếu trường bắt buộc '{req}'"))

    if diagnostics:
        return ProfileValidationResult(is_valid=False, diagnostics=diagnostics)

    try:
        opened_dt = normalize_timestamp(record["opened_at"])
    except ValueError as exc:
        reason = str(exc)
        if "múi giờ" in reason:
            diagnostics.append(ParserDiagnostic(row=row, field="opened_at", reason="opened_at phải có thông tin múi giờ (UTC)"))
        else:
            diagnostics.append(ParserDiagnostic(row=row, field="opened_at", reason="Định dạng opened_at không hợp lệ"))

    if diagnostics:
        return ProfileValidationResult(is_valid=False, diagnostics=diagnostics)

    normalized: dict[str, Any] = {
        "ticket_id": str(record["ticket_id"]).strip(),
        "system": str(record["system"]).strip(),
        "status": str(record["status"]).lower().strip(),
        "priority": str(record["priority"]).upper().strip(),
        "opened_at": opened_dt.isoformat(),
        "resolved_at": record.get("resolved_at"),
        "assignee": record.get("assignee"),
    }
    for opt in ("title", "description", "category"):
        if opt in record:
            normalized[opt] = record[opt]

    return ProfileValidationResult(is_valid=True, normalized_data=normalized)


def validate_incident_record(row: int, record: dict[str, Any]) -> ProfileValidationResult:
    diagnostics: list[ParserDiagnostic] = []
    for req in ("incident_id", "system", "status", "priority", "created_at"):
        if req not in record or not record[req]:
            diagnostics.append(ParserDiagnostic(row=row, field=req, reason=f"Thiếu trường bắt buộc '{req}'"))

    if diagnostics:
        return ProfileValidationResult(is_valid=False, diagnostics=diagnostics)

    try:
        created_dt = normalize_timestamp(record["created_at"])
        created_str = record["created_at"]
    except ValueError as exc:
        return ProfileValidationResult(
            is_valid=False,
            diagnostics=[ParserDiagnostic(row=row, field="created_at", reason=str(exc))],
        )

    normalized: dict[str, Any] = {
        "incident_id": str(record["incident_id"]).strip(),
        "system": str(record["system"]).strip(),
        "status": str(record["status"]).lower().strip(),
        "priority": str(record["priority"]).upper().strip(),
        "created_at": created_str,
        "confirmed_cause": record.get("confirmed_cause"),
    }
    for opt in ("resolved_at", "impact_summary", "order_ids"):
        if opt in record:
            normalized[opt] = record[opt]

    return ProfileValidationResult(is_valid=True, normalized_data=normalized)


def validate_operations_table_record(row: int, record: dict[str, Any]) -> ProfileValidationResult:
    diagnostics: list[ParserDiagnostic] = []
    for req in ("entity_id", "entity_type", "status", "updated_at"):
        if req not in record or not record[req]:
            diagnostics.append(ParserDiagnostic(row=row, field=req, reason=f"Thiếu trường bắt buộc '{req}'"))

    if diagnostics:
        return ProfileValidationResult(is_valid=False, diagnostics=diagnostics)

    try:
        _ = normalize_timestamp(record["updated_at"])
    except ValueError as exc:
        return ProfileValidationResult(
            is_valid=False,
            diagnostics=[ParserDiagnostic(row=row, field="updated_at", reason=str(exc))],
        )

    normalized: dict[str, Any] = {
        "entity_id": str(record["entity_id"]).strip(),
        "entity_type": str(record["entity_type"]).strip(),
        "status": str(record["status"]).strip(),
        "updated_at": record["updated_at"],
    }
    for opt in ("payload", "notes"):
        if opt in record:
            normalized[opt] = record[opt]

    return ProfileValidationResult(is_valid=True, normalized_data=normalized)


def validate_records(
    profile_id: str,
    raw_records: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], tuple[ParserDiagnostic, ...], bool]:
    """Kiểm tra và chuẩn hóa toàn bộ các bản ghi theo profile đã chọn."""
    profile = get_profile(profile_id)
    normalized_list: list[dict[str, Any]] = []
    all_diagnostics: list[ParserDiagnostic] = []
    is_valid = True

    record_validators = {
        "log": validate_log_record,
        "ticket": validate_ticket_record,
        "incident": validate_incident_record,
        "operations_table": validate_operations_table_record,
    }

    if profile_id not in record_validators:
        # Document hoặc generic profile
        return raw_records, (), True

    validator = record_validators[profile_id]
    for idx, rec in enumerate(raw_records, start=1):
        res = validator(idx, rec)
        if not res.is_valid:
            is_valid = False
            all_diagnostics.extend(res.diagnostics)
        else:
            if isinstance(res.normalized_data, dict):
                normalized_list.append(res.normalized_data)

    return normalized_list, tuple(all_diagnostics), is_valid

import pytest
from app.modules.tickets.validator import TicketSchemaValidator
from app.modules.tickets.contracts import SystemEnum, SeverityEnum


@pytest.fixture
def validator():
    return TicketSchemaValidator()


def test_validate_valid_json(validator):
    json_content = """
    [
        {
            "ticket_id": "TCK-001",
            "order_id": "DH001",
            "timestamp": "2026-10-14T08:30:00Z",
            "system": "WMS",
            "severity": "P1",
            "description": "Lỗi đơn hàng không đồng bộ sang TMS sau khi đóng gói"
        },
        {
            "ticket_id": "TCK-002",
            "order_id": "DH010",
            "timestamp": "2026-10-14T09:15:00+07:00",
            "system": "TMS",
            "severity": "P3",
            "description": "Cập nhật biển số xe điều phối chậm 15 phút"
        }
    ]
    """
    result = validator.validate_json(json_content)
    assert result.is_valid is True
    assert result.total_rows == 2
    assert len(result.tickets) == 2
    assert result.tickets[0].ticket_id == "TCK-001"
    assert result.tickets[0].system == SystemEnum.WMS
    assert result.tickets[0].severity == SeverityEnum.P1
    assert result.tickets[1].order_id == "DH010"
    assert len(result.errors) == 0


def test_validate_invalid_json_missing_fields(validator):
    json_content = """
    [
        {
            "ticket_id": "TCK-001",
            "timestamp": "2026-10-14T08:30:00Z",
            "system": "WMS",
            "severity": "P1",
            "description": "Thiếu mã order_id"
        }
    ]
    """
    result = validator.validate_json(json_content)
    assert result.is_valid is False
    assert len(result.tickets) == 0
    assert len(result.errors) >= 1
    assert result.errors[0].line == 1
    assert result.errors[0].field == "order_id"
    assert "Thiếu trường bắt buộc" in result.errors[0].message


def test_validate_invalid_json_syntax(validator):
    result = validator.validate_json("{not valid json}")
    assert result.is_valid is False
    assert len(result.errors) == 1
    assert result.errors[0].line == 1
    assert "không hợp lệ" in result.errors[0].message


def test_validate_valid_csv(validator):
    csv_content = """ticket_id,order_id,timestamp,system,severity,description
TCK-001,DH001,2026-10-14T08:30:00Z,WMS,P1,Lỗi đóng gói đơn hàng
TCK-002,DH002,2026-10-14T08:45:00Z,API_GATEWAY,P2,Lỗi timeout 504 khi gọi TMS
"""
    result = validator.validate_csv(csv_content)
    assert result.is_valid is True
    assert result.total_rows == 2
    assert len(result.tickets) == 2
    assert result.tickets[0].ticket_id == "TCK-001"
    assert result.tickets[1].system == SystemEnum.API_GATEWAY
    assert len(result.errors) == 0


def test_validate_csv_missing_header_columns(validator):
    csv_content = """ticket_id,order_id,system
TCK-001,DH001,WMS
"""
    result = validator.validate_csv(csv_content)
    assert result.is_valid is False
    assert len(result.errors) == 1
    assert result.errors[0].line == 1
    assert "thiếu các cột bắt buộc" in result.errors[0].message.lower()


def test_validate_csv_invalid_row_severity(validator):
    csv_content = """ticket_id,order_id,timestamp,system,severity,description
TCK-001,DH001,2026-10-14T08:30:00Z,WMS,P99,Lỗi mức độ nghiêm trọng không có trong enum
"""
    result = validator.validate_csv(csv_content)
    assert result.is_valid is False
    assert len(result.tickets) == 0
    assert len(result.errors) >= 1
    assert result.errors[0].line == 2
    assert result.errors[0].field == "severity"


def test_validate_csv_sanitizes_formula_injection(validator):
    csv_content = """ticket_id,order_id,timestamp,system,severity,description
TCK-001,DH001,2026-10-14T08:30:00Z,WMS,P1,=SUM(A1:A10) test formula injection
"""
    result = validator.validate_csv(csv_content)
    assert result.is_valid is True
    assert not result.tickets[0].description.startswith("=")
    assert "SUM(A1:A10)" in result.tickets[0].description

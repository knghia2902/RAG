import pytest
from app.modules.tickets.service import TicketService, MAX_TICKET_FILE_SIZE_BYTES
from app.modules.tickets.contracts import SystemEnum, SeverityEnum


@pytest.fixture
def service():
    return TicketService()


def test_process_uploaded_json_file(service):
    content = b"""[
        {
            "ticket_id": "TCK-001",
            "order_id": "DH001",
            "timestamp": "2026-10-14T08:30:00Z",
            "system": "WMS",
            "severity": "P1",
            "description": "Don hang khong dong bo sang TMS"
        }
    ]"""
    result = service.process_uploaded_ticket_file("tickets.json", content)
    assert result.is_valid is True
    assert len(result.tickets) == 1
    assert result.tickets[0].ticket_id == "TCK-001"


def test_process_uploaded_csv_with_bom(service):
    content = "\ufeffticket_id,order_id,timestamp,system,severity,description\nTCK-002,DH002,2026-10-14T08:30:00Z,TMS,P2,Loi dieu phoi xe\n".encode("utf-8")
    result = service.process_uploaded_ticket_file("tickets.csv", content)
    assert result.is_valid is True
    assert len(result.tickets) == 1
    assert result.tickets[0].system == SystemEnum.TMS
    assert result.tickets[0].severity == SeverityEnum.P2


def test_process_uploaded_unsupported_extension(service):
    with pytest.raises(ValueError, match="không được hỗ trợ"):
        service.process_uploaded_ticket_file("tickets.xlsx", b"some binary data")


def test_process_uploaded_oversized_file(service):
    oversized = b"a" * (MAX_TICKET_FILE_SIZE_BYTES + 1024)
    with pytest.raises(ValueError, match="vượt quá giới hạn"):
        service.process_uploaded_ticket_file("big.json", oversized)

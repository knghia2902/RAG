import io
from uuid import uuid4
import pytest
from fastapi import HTTPException
from app.modules.tickets.service import TicketService, MAX_TICKET_FILE_SIZE_BYTES
from app.llm.contracts import GenerationRequest, LLMProvider, GenerationResult
from app.llm.errors import LLMTimeoutError, LLMServiceError
from app.llm.generation import GroundedGenerator
from app.rag.contracts import EvidenceChunk, SourceLocator


def test_upload_file_size_limit_enforced(client, admin):
    """D-09 & EVAL-03: Files exceeding upload limits are rejected with informative errors."""
    # 1. Test ticket upload exceeding 5MB limit (600,000 rows * 10 bytes = ~6MB)
    oversized_content = b"header1,header2\n" + (b"row1,row2\n" * 600000)
    assert len(oversized_content) > MAX_TICKET_FILE_SIZE_BYTES

    ticket_service = TicketService()
    with pytest.raises(ValueError) as excinfo:
        ticket_service.process_uploaded_ticket_file("large_tickets.csv", oversized_content)
    assert "vượt quá giới hạn cho phép" in str(excinfo.value)

    # 2. Test API ticket endpoint rejection with oversized payload
    files = {"file": ("large_tickets.csv", io.BytesIO(oversized_content), "text/csv")}
    res = client.post(
        "/api/v1/incidents/upload-ticket",
        files=files,
        headers={
            "Origin": "http://next-test:3000",
            "X-Requested-With": "RAG-Web",
            "X-CSRF-Token": admin["X-CSRF-Token"],
        },
    )
    assert res.status_code == 400
    assert "vượt quá giới hạn" in res.json()["detail"]


class TimeoutSimulatingLLMProvider(LLMProvider):
    """Simulates an LLM Provider timing out on generation."""
    def generate(self, request: GenerationRequest) -> GenerationResult:
        raise TimeoutError("OpenAI API call exceeded 30.0s client timeout")


def test_network_timeout_handling_sys05():
    """D-09 & SYS-05: Timeout errors are caught and raised as explicit LLMTimeoutError per SYS-05."""
    generator = GroundedGenerator(llm_provider=TimeoutSimulatingLLMProvider())

    dummy_chunk = EvidenceChunk(
        dataset_id=uuid4(),
        locator=SourceLocator(source_id=uuid4(), source_version=1),
        text="Sample log context",
    )

    with pytest.raises(LLMTimeoutError) as excinfo:
        generator.generate_answer(
            question="Nguyên nhân sự cố đơn hàng DH001?",
            evidence=(dummy_chunk,),
        )

    assert "Quá thời gian chờ" in str(excinfo.value)


class HardFailingLLMProvider(LLMProvider):
    """Simulates complete service outage / 500 error."""
    def generate(self, request: GenerationRequest) -> GenerationResult:
        raise RuntimeError("External AI service unreachable: Connection refused (502)")


def test_graceful_error_without_mock_content():
    """D-09 & SYS-05: Outages must surface transparent error information, NEVER fabricating mock metrics or hallucinations."""
    generator = GroundedGenerator(llm_provider=HardFailingLLMProvider())

    dummy_chunk = EvidenceChunk(
        dataset_id=uuid4(),
        locator=SourceLocator(source_id=uuid4(), source_version=1),
        text="Sample log context",
    )

    # Verify that external outage is explicitly raised as LLMServiceError
    # rather than catching and returning fake numbers or hallucinations
    with pytest.raises(LLMServiceError) as excinfo:
        generator.generate_answer(
            question="Tính tổng số lượng đơn hàng lỗi?",
            evidence=(dummy_chunk,),
        )

    assert "Lỗi dịch vụ AI Provider" in str(excinfo.value)

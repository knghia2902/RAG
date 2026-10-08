from uuid import uuid4
import pytest
from app.llm.contracts import GenerationRequest, GenerationResult, LLMProvider
from app.llm.errors import LLMTimeoutError, format_llm_error_response
from app.llm.generation import GroundedGenerator
from app.providers.fake import FakeLLMAdapter
from app.rag.contracts import EvidenceChunk, SourceLocator


def create_test_chunk(text: str, line: int = 1) -> EvidenceChunk:
    return EvidenceChunk(
        dataset_id=uuid4(),
        locator=SourceLocator(
            source_id=uuid4(),
            source_version=1,
            line_start=line,
            line_end=line + 5,
        ),
        text=text,
    )


def test_grounded_generation_with_citations():
    """Xác minh RAG-01 & RAG-04: Câu trả lời có cấu trúc và trích dẫn chuẩn."""
    adapter = FakeLLMAdapter()
    generator = GroundedGenerator(llm_provider=adapter)

    c1 = create_test_chunk("Đơn hàng DH001 bị lỗi cảm biến tại cổng 3")
    evidence = [c1]

    result = generator.generate_answer(
        question="Tình trạng đơn DH001",
        evidence=evidence,
    )

    assert "[1]" in result.answer_text
    assert len(result.citations) == 1
    assert result.citations[0].citation_index == 1
    assert result.citations[0].source_id == c1.locator.source_id
    assert result.has_uncertainty is False
    assert result.has_conflict is False


def test_egress_secret_masking_before_provider_call():
    """Xác minh SYS-03: Che giấu secret trước khi gọi API Provider."""
    captured_requests = []

    class InspectingLLMAdapter(LLMProvider):
        def generate(self, request: GenerationRequest) -> GenerationResult:
            captured_requests.append(request)
            return GenerationResult(
                text=f"Đã kiểm tra [1]: {request.question}",
                citations=(request.evidence[0].locator,),
            )

    adapter = InspectingLLMAdapter()
    generator = GroundedGenerator(llm_provider=adapter)

    # Chứa API key sk-..., Bearer token và mật khẩu trong câu hỏi và evidence
    sensitive_chunk = create_test_chunk(
        "Kết nối API kho với Bearer 1234567890abcdef1234567890 và token=secret_password_123"
    )
    result = generator.generate_answer(
        question="Tra cứu khóa sk-12345678901234567890123456 cho đơn DH001",
        evidence=[sensitive_chunk],
    )

    assert len(captured_requests) == 1
    req = captured_requests[0]
    # Khóa bí mật trong câu hỏi phải bị che
    assert "sk-12345678901234567890123456" not in req.question
    assert "sk-[REDACTED]" in req.question

    # Token trong evidence phải bị che
    assert "1234567890abcdef1234567890" not in req.evidence[0].text
    assert "Bearer [REDACTED]" in req.evidence[0].text


def test_context_token_budget_truncation():
    """Xác minh SYS-03 & T-03-09: Giới hạn token budget không để tràn context."""
    captured_requests = []

    class InspectingLLMAdapter(LLMProvider):
        def generate(self, request: GenerationRequest) -> GenerationResult:
            captured_requests.append(request)
            return GenerationResult(
                text="Xử lý theo [1]",
                citations=(request.evidence[0].locator,),
            )

    adapter = InspectingLLMAdapter()
    # Giới hạn rất nhỏ: chỉ 50 tokens (khoảng 150 ký tự)
    generator = GroundedGenerator(llm_provider=adapter, max_context_tokens=50)

    chunks = [create_test_chunk(f"Bản ghi số {i} " + "dữ liệu dài " * 20, line=i + 1) for i in range(10)]
    result = generator.generate_answer(
        question="Tổng hợp dữ liệu",
        evidence=chunks,
    )

    req = captured_requests[0]
    # Số lượng chunks được đưa vào context phải bị cắt giảm để không vượt quá 50 tokens
    assert len(req.evidence) < len(chunks)


def test_uncertainty_handling_when_evidence_empty():
    """Xác minh RAG-05: Khi không có bằng chứng, trả lời nêu rõ thiếu dữ liệu."""
    adapter = FakeLLMAdapter()
    generator = GroundedGenerator(llm_provider=adapter)

    result = generator.generate_answer(
        question="Kiểm tra đơn hàng DH999",
        evidence=[],
    )

    assert result.has_uncertainty is True
    assert result.has_conflict is False
    assert len(result.citations) == 0
    assert "Không tìm thấy thông tin xác thực" in result.answer_text


def test_conflict_detection_flag():
    """Xác minh RAG-05: Khi LLM chỉ ra mâu thuẫn, gán cờ has_conflict = True."""
    class ConflictingLLMAdapter(LLMProvider):
        def generate(self, request: GenerationRequest) -> GenerationResult:
            return GenerationResult(
                text="Phát hiện mâu thuẫn giữa các nguồn: [1] ghi nhận đơn đã hoàn thành nhưng [2] báo lỗi kẹt hàng.",
                citations=(request.evidence[0].locator, request.evidence[1].locator),
            )

    adapter = ConflictingLLMAdapter()
    generator = GroundedGenerator(llm_provider=adapter)

    c1 = create_test_chunk("Trạng thái đơn: Hoàn thành", line=1)
    c2 = create_test_chunk("Trạng thái đơn: Thất bại do kẹt hàng", line=10)

    result = generator.generate_answer(
        question="Kiểm tra trạng thái đơn",
        evidence=[c1, c2],
    )

    assert result.has_conflict is True
    assert "[1]" in result.answer_text
    assert "[2]" in result.answer_text


def test_timeout_error_handling_and_formatting():
    """Xác minh SYS-05: Xử lý ngoại lệ timeout bền bỉ, thông điệp tiếng Việt thân thiện."""
    class TimeoutLLMAdapter(LLMProvider):
        def generate(self, request: GenerationRequest) -> GenerationResult:
            raise TimeoutError("Connection to OpenAI timed out after 30s")

    adapter = TimeoutLLMAdapter()
    generator = GroundedGenerator(llm_provider=adapter)

    c1 = create_test_chunk("Dữ liệu thử nghiệm")
    with pytest.raises(LLMTimeoutError) as exc_info:
        generator.generate_answer(
            question="Kiểm tra",
            evidence=[c1],
        )

    # Kiểm tra format phản hồi lỗi thân thiện
    formatted = format_llm_error_response(exc_info.value)
    assert formatted["error"] is True
    assert formatted["category"] == "timeout"
    assert formatted["retryable"] is True
    assert "Thời gian phản hồi" in formatted["detail"]

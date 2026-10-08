from uuid import uuid4
import pytest
from app.llm.citation_verifier import CitationVerifier
from app.rag.contracts import EvidenceChunk, SourceLocator


def create_chunk(text: str, line: int = 1) -> EvidenceChunk:
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


def test_valid_citations_retained_and_mapped():
    c1 = create_chunk("Quy trình kiểm tra cổng số 3", line=1)
    c2 = create_chunk("Hướng dẫn khởi động lại cảm biến quang", line=10)
    evidence = [c1, c2]

    raw_answer = "Lỗi xảy ra tại cổng số 3 [1]. Kỹ thuật viên cần khởi động lại cảm biến quang [2]."
    sanitized_answer, citations = CitationVerifier.verify_citations(raw_answer, evidence)

    assert "[1]" in sanitized_answer
    assert "[2]" in sanitized_answer
    assert len(citations) == 2
    assert citations[0].citation_index == 1
    assert citations[0].excerpt_text == c1.text
    assert citations[0].source_id == c1.locator.source_id
    assert citations[1].citation_index == 2
    assert citations[1].excerpt_text == c2.text
    assert citations[1].source_id == c2.locator.source_id


def test_hallucinated_citations_scrubbed_from_answer():
    c1 = create_chunk("Thông tin đơn hàng DH001")
    evidence = [c1]

    # LLM tự bịa ra citation [5] và [99] khi context chỉ có 1 chunk (RAG-04)
    raw_answer = "Theo quy định bảo hành [5], hàng hóa sẽ được hoàn tiền [99]."
    sanitized_answer, citations = CitationVerifier.verify_citations(raw_answer, evidence)

    assert "[5]" not in sanitized_answer
    assert "[99]" not in sanitized_answer
    assert len(citations) == 0


def test_mixed_valid_and_hallucinated_citations():
    c1 = create_chunk("Đơn hàng DH001 bị kẹt tại máng chuyền")
    c2 = create_chunk("Tốc độ xử lý băng tải là 1.5m/s")
    evidence = [c1, c2]

    raw_answer = "Đơn hàng DH001 bị kẹt [1], nhân viên xử lý không đúng SOP [8]."
    sanitized_answer, citations = CitationVerifier.verify_citations(raw_answer, evidence)

    assert "[1]" in sanitized_answer
    assert "[8]" not in sanitized_answer
    assert len(citations) == 1
    assert citations[0].citation_index == 1


def test_duplicate_citations_deduplicated_in_list():
    c1 = create_chunk("Hướng dẫn xử lý lỗi ERR-502")
    evidence = [c1]

    raw_answer = "Phát hiện lỗi ERR-502 [1]. Cần làm theo tài liệu hướng dẫn [1]."
    sanitized_answer, citations = CitationVerifier.verify_citations(raw_answer, evidence)

    assert "[1]" in sanitized_answer
    assert len(citations) == 1
    assert citations[0].citation_index == 1

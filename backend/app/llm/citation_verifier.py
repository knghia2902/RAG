import re
from typing import Sequence
from app.llm.contracts import CitationItem
from app.rag.contracts import EvidenceChunk


class CitationVerifier:
    """Xác thực và làm sạch trích dẫn nguồn phía máy chủ (RAG-04).

    Ngăn chặn LLM hallucination bịa đặt số trích dẫn không có trong evidence context.
    """

    @staticmethod
    def verify_citations(
        raw_answer: str,
        evidence: Sequence[EvidenceChunk],
    ) -> tuple[str, list[CitationItem]]:
        if not raw_answer:
            return "", []

        num_chunks = len(evidence)
        valid_citations: dict[int, CitationItem] = {}

        # Hàm thay thế lọc bỏ các citation bất hợp lệ
        def replace_citation(match: re.Match) -> str:
            citation_str = match.group(1)
            try:
                idx = int(citation_str)
            except ValueError:
                return ""

            if 1 <= idx <= num_chunks:
                chunk = evidence[idx - 1]
                if idx not in valid_citations:
                    valid_citations[idx] = CitationItem(
                        citation_index=idx,
                        dataset_id=chunk.dataset_id,
                        source_id=chunk.locator.source_id,
                        source_version=chunk.locator.source_version,
                        locator=chunk.locator,
                        excerpt_text=chunk.text,
                    )
                return f"[{idx}]"
            else:
                # Hallucinated citation: loại bỏ thẻ [n] khỏi văn bản
                return ""

        # Thay thế và làm sạch các thẻ trích dẫn trong văn bản trả lời
        sanitized_answer = re.sub(r"\[(\d+)\]", replace_citation, raw_answer)

        # Chuẩn hóa khoảng trắng sau khi loại bỏ thẻ
        sanitized_answer = re.sub(r"\s{2,}", " ", sanitized_answer).strip()

        # Sắp xếp danh sách citation theo thứ tự xuất hiện
        sorted_citations = [valid_citations[k] for k in sorted(valid_citations.keys())]

        return sanitized_answer, sorted_citations

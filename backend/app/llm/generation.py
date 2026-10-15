import re
from typing import Sequence
from app.llm.citation_verifier import CitationVerifier
from app.llm.contracts import CitationItem, GenerationRequest, GroundedAnswer, LLMProvider
from app.llm.errors import (
    LLMAuthenticationError,
    LLMBaseError,
    LLMQuotaExceededError,
    LLMServiceError,
    LLMTimeoutError,
)
from app.llm.secret_masking import mask_secrets
from app.rag.contracts import EvidenceChunk

UNCERTAINTY_PHRASES = [
    "không đủ dữ liệu",
    "chưa đủ cơ sở",
    "không tìm thấy",
    "không có thông tin",
    "chưa xác định",
    "thiếu thông tin",
    "không thể kết luận",
    "chưa có bằng chứng",
]

CONFLICT_PHRASES = [
    "mâu thuẫn",
    "trái ngược",
    "bất đồng",
    "không thống nhất",
    "xung đột",
]


def detect_uncertainty(text: str) -> bool:
    """Phát hiện trạng thái thiếu dữ liệu hoặc không chắc chắn trong câu trả lời (RAG-05)."""
    if not text:
        return True
    lower = text.lower()
    return any(p in lower for p in UNCERTAINTY_PHRASES)


def detect_conflict(text: str) -> bool:
    """Phát hiện mâu thuẫn giữa các nguồn tài liệu trong câu trả lời (RAG-05)."""
    if not text:
        return False
    lower = text.lower()
    return any(p in lower for p in CONFLICT_PHRASES)


class GroundedGenerator:
    """Bộ tạo câu trả lời dựa trên bằng chứng, kiểm soát token budget,

    che giấu secret và thẩm định trích dẫn nguồn (RAG-01, RAG-04, RAG-05, SYS-03, SYS-05).
    """

    def __init__(self, llm_provider: LLMProvider, max_context_tokens: int = 4000):
        self.llm_provider = llm_provider
        self.max_context_tokens = max_context_tokens

    def generate_answer(
        self,
        question: str,
        evidence: Sequence[EvidenceChunk],
        history: list[dict] | None = None,
        images: list[dict] | None = None,
    ) -> GroundedAnswer:
        # 1. Che giấu secrets trong câu hỏi trước khi xử lý (SYS-03)
        masked_question = mask_secrets(question)

        # 2. Xử lý trường hợp không tìm thấy bằng chứng phù hợp
        if not evidence:
            return GroundedAnswer(
                answer_text="Không tìm thấy thông tin xác thực từ các nguồn dữ liệu được cấp quyền. Vui lòng cung cấp thêm từ khóa hoặc kiểm tra lại quyền truy cập tài liệu.",
                citations=(),
                has_uncertainty=True,
                has_conflict=False,
            )

        # 3. Cắt tỉa evidence theo token budget và che giấu secrets trước egress (SYS-03)
        max_chars = self.max_context_tokens * 3
        current_chars = 0
        selected_evidence: list[EvidenceChunk] = []

        for chunk in evidence:
            masked_chunk_text = mask_secrets(chunk.text)
            chunk_len = len(masked_chunk_text)
            if current_chars + chunk_len > max_chars and selected_evidence:
                break
            selected_chunk = EvidenceChunk(
                dataset_id=chunk.dataset_id,
                locator=chunk.locator,
                text=masked_chunk_text,
                images=getattr(chunk, "images", ()),
            )
            selected_evidence.append(selected_chunk)
            current_chars += chunk_len

        # Thu thập danh sách ảnh (ưu tiên tham số images, hoặc lấy từ chunks đã chọn)
        image_list = list(images or [])
        if not image_list:
            seen_img_ids = set()
            for chk in selected_evidence:
                for img in getattr(chk, "images", ()):
                    iid = img.get("image_id")
                    if iid and iid not in seen_img_ids:
                        seen_img_ids.add(iid)
                        image_list.append(img)
                        if len(image_list) >= 3:
                            break
                if len(image_list) >= 3:
                    break

        # 4. Gọi LLM Provider với xử lý ngoại lệ bền bỉ (SYS-05)
        request = GenerationRequest(
            question=masked_question,
            evidence=tuple(selected_evidence),
            images=tuple(image_list[:3]),
        )

        try:
            raw_result = self.llm_provider.generate(request)
        except (TimeoutError, TimeoutException := Exception) as err:
            err_msg = str(err).lower()
            if "timeout" in err_msg or isinstance(err, TimeoutError):
                raise LLMTimeoutError(f"Quá thời gian chờ phản hồi từ AI Provider: {err}") from err
            elif "quota" in err_msg or "rate limit" in err_msg or "429" in err_msg:
                raise LLMQuotaExceededError(f"Vượt giới hạn lượt gọi AI Provider: {err}") from err
            elif "auth" in err_msg or "api key" in err_msg or "401" in err_msg or "403" in err_msg:
                raise LLMAuthenticationError(f"Lỗi xác thực API Key AI Provider: {err}") from err
            else:
                raise LLMServiceError(f"Lỗi dịch vụ AI Provider: {err}") from err

        # 5. Thẩm định và làm sạch trích dẫn phía server (RAG-04)
        sanitized_answer, valid_citations = CitationVerifier.verify_citations(
            raw_answer=raw_result.text,
            evidence=selected_evidence,
        )

        # 6. Gán cờ phát hiện thiếu thông tin hoặc mâu thuẫn (RAG-05)
        has_uncertainty = detect_uncertainty(sanitized_answer)
        has_conflict = detect_conflict(sanitized_answer)

        return GroundedAnswer(
            answer_text=sanitized_answer,
            citations=tuple(valid_citations),
            has_uncertainty=has_uncertainty,
            has_conflict=has_conflict,
        )

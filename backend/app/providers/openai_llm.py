import base64
import logging
import os
import re
from typing import Sequence
import httpx
import openai
from app.llm.contracts import GenerationRequest, GenerationResult, LLMProvider
from app.rag.contracts import EvidenceChunk, SourceLocator

logger = logging.getLogger(__name__)


class OpenAILLMAdapter(LLMProvider):
    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4o-mini",
        base_url: str | None = None,
        timeout: float = 30.0,
        max_tokens: int = 2048,
    ):
        self.api_key = api_key
        self.model = model
        self.base_url = base_url
        self.timeout = timeout
        self.max_tokens = max_tokens
        client_kwargs = {
            "api_key": api_key,
            "timeout": timeout,
            "http_client": httpx.Client(timeout=timeout),
        }
        if base_url:
            client_kwargs["base_url"] = base_url
        self._client = (
            openai.OpenAI(**client_kwargs)
            if api_key
            else None
        )

    def prepare_multimodal_images(self, images: Sequence[dict] | None) -> list[dict]:
        """Chuẩn bị và chuyển đổi tối đa 3 hình ảnh thành định dạng base64 payload.
        
        Giới hạn cứng tối đa 3 ảnh để kiểm soát token budget và latency (T-07-04, D-03).
        """
        if not images:
            return []

        prepared: list[dict] = []
        for img in images[:3]:
            mime = img.get("mime_type") or "image/png"
            b64 = img.get("b64") or img.get("base64_data")
            if not b64 and img.get("storage_path"):
                storage_path = img["storage_path"]
                if os.path.exists(storage_path):
                    try:
                        with open(storage_path, "rb") as f:
                            b64 = base64.b64encode(f.read()).decode("utf-8")
                    except Exception as exc:
                        logger.warning("Không thể đọc tệp ảnh %s: %s", storage_path, exc)
            if b64:
                prepared.append({
                    "image_id": str(img.get("image_id", "")),
                    "mime_type": mime,
                    "b64": b64,
                    "caption": img.get("caption"),
                    "api_url": img.get("api_url"),
                })
        return prepared

    def build_multimodal_messages(
        self,
        question: str,
        evidence: Sequence[EvidenceChunk],
        images: Sequence[dict] | None = None,
    ) -> list[dict]:
        """Xây dựng payload tin nhắn cho OpenAI / Google Gemini Multimodal Vision (D-03, D-04)."""
        evidence_lines = []
        for i, chunk in enumerate(evidence, start=1):
            evidence_lines.append(f"[Bằng chứng {i}]: {chunk.text}")
        evidence_text = "\n\n".join(evidence_lines)

        valid_images = self.prepare_multimodal_images(images)

        system_prompt = (
            "Bạn là trợ lý phân tích tri thức và sự cố logistics chuyên nghiệp. "
            "Chỉ trả lời dựa trên các đoạn bằng chứng được cung cấp bên dưới. "
            "Sau mỗi khẳng định hoặc kết luận, hãy trích dẫn số thứ tự bằng chứng dạng [1], [2]. "
            "Nếu bằng chứng không đủ để trả lời chắc chắn, hãy nêu rõ các điểm chưa biết. "
            "Nếu có thông tin mâu thuẫn giữa các bằng chứng, hãy chỉ rõ sự mâu thuẫn đó. "
            "Tuyệt đối không suy đoán giả thuyết thành nguyên nhân đã xác nhận."
        )

        user_prompt_text = (
            f"Các bằng chứng được cung cấp:\n{evidence_text}\n\n"
            f"Câu hỏi: {question}\n\n"
            f"Hãy trả lời bằng tiếng Việt và trích dẫn số thứ tự bằng chứng chính xác."
        )

        if valid_images:
            system_prompt += (
                " Nếu trong ngữ cảnh có hình ảnh hoặc sơ đồ kỹ thuật, hãy quan sát kỹ các thông số/chi tiết "
                "trong hình ảnh để trả lời chính xác và chèn trích dẫn ảnh bằng cú pháp Markdown: ![Mô tả ảnh](IMAGE_API_URL)."
            )
            img_desc_lines = ["\nDanh sách hình ảnh/sơ đồ kỹ thuật đính kèm:"]
            for idx, img in enumerate(valid_images, start=1):
                cap = img.get("caption") or f"Hình ảnh {idx}"
                url = img.get("api_url") or f"/images/{img.get('image_id')}"
                img_desc_lines.append(f"- Ảnh {idx}: {cap} (URL trích dẫn: {url})")
            user_prompt_text += "\n" + "\n".join(img_desc_lines)

            user_content: list[dict] = [{"type": "text", "text": user_prompt_text}]
            for img in valid_images:
                user_content.append({
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:{img['mime_type']};base64,{img['b64']}"
                    }
                })
        else:
            user_content = user_prompt_text

        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ]

    def generate(self, request: GenerationRequest, images: list[dict] | None = None) -> GenerationResult:
        if not self._client:
            provider_name = "Gemini" if "gemini" in self.model.lower() or "google" in (self.base_url or "").lower() else "OpenAI"
            raise RuntimeError(f"{provider_name} API key chưa được cấu hình cho LLM Provider.")

        # Lấy danh sách ảnh từ tham số, request.images hoặc từ các chunks
        img_list = list(images or [])
        if not img_list and getattr(request, "images", None):
            img_list = list(request.images)
        if not img_list and request.evidence:
            for chk in request.evidence:
                for img in getattr(chk, "images", ()):
                    img_list.append(img)

        messages = self.build_multimodal_messages(
            question=request.question,
            evidence=request.evidence,
            images=img_list,
        )

        try:
            response = self._client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=self.max_tokens,
                timeout=self.timeout,
            )
            raw_text = response.choices[0].message.content or ""

            # Extract citations: look for [1], [2] in text and map to request.evidence
            cited_indices = set(int(m) for m in re.findall(r"\[(\d+)\]", raw_text))
            citations: list[SourceLocator] = []
            for idx in sorted(cited_indices):
                if 1 <= idx <= len(request.evidence):
                    citations.append(request.evidence[idx - 1].locator)

            # If no citations were explicitly bracketed but evidence was provided, include at least the first locator if text is non-empty
            if not citations and request.evidence and raw_text:
                citations.append(request.evidence[0].locator)

            return GenerationResult(
                text=raw_text,
                citations=tuple(citations),
            )
        except openai.APITimeoutError as e:
            provider_name = "Gemini" if "gemini" in self.model.lower() or "google" in (self.base_url or "").lower() else "OpenAI"
            raise TimeoutError(f"{provider_name} LLM API timeout sau {self.timeout}s: {e}") from e
        except openai.APIError as e:
            provider_name = "Gemini" if "gemini" in self.model.lower() or "google" in (self.base_url or "").lower() else "OpenAI"
            raise RuntimeError(f"Lỗi {provider_name} LLM API: {e.message}") from e

    def generate_grounded_answer(
        self,
        question: str,
        evidence: Sequence[EvidenceChunk],
        images: list[dict] | None = None,
    ) -> GenerationResult:
        """Hàm tạo câu trả lời hỗ trợ ảnh trích xuất trực tiếp."""
        request = GenerationRequest(
            question=question,
            evidence=tuple(evidence),
            images=tuple(images or ()),
        )
        return self.generate(request, images=images)


import re
from typing import Sequence
import httpx
import openai
from app.llm.contracts import GenerationRequest, GenerationResult, LLMProvider
from app.rag.contracts import SourceLocator


class OpenAILLMAdapter(LLMProvider):
    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4o-mini",
        timeout: float = 30.0,
        max_tokens: int = 2048,
    ):
        self.api_key = api_key
        self.model = model
        self.timeout = timeout
        self.max_tokens = max_tokens
        self._client = (
            openai.OpenAI(api_key=api_key, timeout=timeout, http_client=httpx.Client(timeout=timeout))
            if api_key
            else None
        )

    def generate(self, request: GenerationRequest) -> GenerationResult:
        if not self._client:
            raise RuntimeError("OpenAI API key chưa được cấu hình cho LLM Provider.")

        # Build evidence context block
        evidence_lines = []
        for i, chunk in enumerate(request.evidence, start=1):
            evidence_lines.append(f"[Bằng chứng {i}]: {chunk.text}")
        evidence_text = "\n\n".join(evidence_lines)

        system_prompt = (
            "Bạn là trợ lý phân tích tri thức và sự cố logistics chuyên nghiệp. "
            "Chỉ trả lời dựa trên các đoạn bằng chứng được cung cấp bên dưới. "
            "Sau mỗi khẳng định hoặc kết luận, hãy trích dẫn số thứ tự bằng chứng dạng [1], [2]. "
            "Nếu bằng chứng không đủ để trả lời chắc chắn, hãy nêu rõ các điểm chưa biết. "
            "Nếu có thông tin mâu thuẫn giữa các bằng chứng, hãy chỉ rõ sự mâu thuẫn đó. "
            "Tuyệt đối không suy đoán giả thuyết thành nguyên nhân đã xác nhận."
        )

        user_content = (
            f"Các bằng chứng được cung cấp:\n{evidence_text}\n\n"
            f"Câu hỏi: {request.question}\n\n"
            f"Hãy trả lời bằng tiếng Việt và trích dẫn số thứ tự bằng chứng chính xác."
        )

        try:
            response = self._client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content},
                ],
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
            raise TimeoutError(f"OpenAI LLM API timeout sau {self.timeout}s: {e}") from e
        except openai.APIError as e:
            raise RuntimeError(f"Lỗi OpenAI LLM API: {e.message}") from e

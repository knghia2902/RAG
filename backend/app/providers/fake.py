import hashlib
import math
from typing import Sequence
from uuid import UUID, uuid4
from app.rag.contracts import EmbeddingIndex, EmbeddingProvider, SourceLocator
from app.llm.contracts import GenerationRequest, GenerationResult, LLMProvider


class FakeEmbeddingAdapter(EmbeddingProvider):
    def __init__(
        self,
        model: str = "fake-embedding-small",
        dimension: int = 1536,
        index_version: UUID | None = None,
    ):
        self.model = model
        self.dimension = dimension
        self._index_version = index_version or uuid4()

    @property
    def index(self) -> EmbeddingIndex:
        return EmbeddingIndex(
            model=self.model,
            dimension=self.dimension,
            index_version=self._index_version,
        )

    def embed(self, texts: tuple[str, ...]) -> tuple[tuple[float, ...], ...]:
        result = []
        for text in texts:
            # Deterministic pseudo-vector using MD5 hash bytes
            h = hashlib.sha256(text.encode("utf-8")).digest()
            raw = []
            for i in range(self.dimension):
                byte_val = h[i % len(h)]
                raw.append((byte_val - 128) / 128.0)
            norm = math.sqrt(sum(x * x for x in raw)) or 1.0
            unit_vec = tuple(round(x / norm, 6) for x in raw)
            result.append(unit_vec)
        return tuple(result)

    def embed_texts(self, texts: Sequence[str]) -> list[list[float]]:
        result = self.embed(tuple(texts))
        return [list(vec) for vec in result]


class FakeLLMAdapter(LLMProvider):
    def __init__(self, model: str = "fake-llm-mini"):
        self.model = model

    def generate(self, request: GenerationRequest) -> GenerationResult:
        if not request.evidence:
            return GenerationResult(
                text="Không tìm thấy thông tin xác thực từ các nguồn dữ liệu được cấp quyền.",
                citations=(),
            )

        # Generate grounded summary mentioning evidence
        first_chunk = request.evidence[0]
        answer = f"Dựa trên tài liệu kiểm tra [1], thông tin liên quan đến '{request.question}': {first_chunk.text[:200]}."
        citations = tuple(e.locator for e in request.evidence[:1])
        return GenerationResult(
            text=answer,
            citations=citations,
        )


FakeLLMProvider = FakeLLMAdapter


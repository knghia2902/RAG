from typing import Sequence
from uuid import UUID, uuid4
import openai
from app.rag.contracts import EmbeddingIndex, EmbeddingProvider


class OpenAIEmbeddingAdapter(EmbeddingProvider):
    def __init__(
        self,
        api_key: str,
        model: str = "text-embedding-3-small",
        dimension: int = 1536,
        index_version: UUID | None = None,
        timeout: float = 30.0,
    ):
        self.api_key = api_key
        self.model = model
        self.dimension = dimension
        self._index_version = index_version or uuid4()
        self.timeout = timeout
        self._client = openai.OpenAI(api_key=api_key, timeout=timeout) if api_key else None

    @property
    def index(self) -> EmbeddingIndex:
        return EmbeddingIndex(
            model=self.model,
            dimension=self.dimension,
            index_version=self._index_version,
        )

    def embed(self, texts: tuple[str, ...]) -> tuple[tuple[float, ...], ...]:
        if not texts:
            return ()
        if not self._client:
            raise RuntimeError("OpenAI API key chưa được cấu hình cho Embedding Provider.")

        try:
            response = self._client.embeddings.create(
                input=list(texts),
                model=self.model,
            )
            return tuple(tuple(item.embedding) for item in response.data)
        except openai.APITimeoutError as e:
            raise TimeoutError(f"OpenAI Embedding API timeout sau {self.timeout}s: {e}") from e
        except openai.APIError as e:
            raise RuntimeError(f"Lỗi OpenAI Embedding API: {e.message}") from e

    def embed_texts(self, texts: Sequence[str]) -> list[list[float]]:
        result = self.embed(tuple(texts))
        return [list(vec) for vec in result]

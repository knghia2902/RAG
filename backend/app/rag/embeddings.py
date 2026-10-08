from typing import Sequence
from uuid import UUID
from app.rag.contracts import EmbeddingIndex, EmbeddingProvider
from app.llm.secret_masking import mask_secrets


class EmbeddingService:
    """RAG embedding service: handles secret masking, batching, and embedding generation.
    Decoupled from database models to maintain strict module boundaries.
    """

    def __init__(self, provider: EmbeddingProvider):
        self.provider = provider

    @property
    def index(self) -> EmbeddingIndex:
        return self.provider.index

    def sanitize_and_embed(self, texts: Sequence[str]) -> list[list[float]]:
        if not texts:
            return []

        # SYS-03: Apply secret masking before embedding egress
        sanitized_texts = [mask_secrets(t) for t in texts]

        # Call provider with tuple of strings
        raw_vectors = self.provider.embed(tuple(sanitized_texts))
        return [list(vec) for vec in raw_vectors]

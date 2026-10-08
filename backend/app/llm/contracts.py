"""Generation only receives selected evidence, separately from embedding APIs."""
from typing import Protocol, runtime_checkable
from pydantic import Field
from app.rag.contracts import BoundaryDTO, EvidenceChunk, SourceLocator


class GenerationRequest(BoundaryDTO):
    question: str = Field(min_length=1, max_length=8000)
    evidence: tuple[EvidenceChunk, ...] = Field(min_length=1, max_length=100)


class GenerationResult(BoundaryDTO):
    text: str = Field(min_length=1, max_length=32000)
    citations: tuple[SourceLocator, ...] = Field(min_length=1, max_length=100)


@runtime_checkable
class LLMProvider(Protocol):
    def generate(self, request: GenerationRequest) -> GenerationResult: ...

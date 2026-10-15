"""Generation only receives selected evidence, separately from embedding APIs."""
from typing import Protocol, runtime_checkable
from uuid import UUID
from pydantic import Field
from app.rag.contracts import BoundaryDTO, EvidenceChunk, SourceLocator


class GenerationRequest(BoundaryDTO):
    question: str = Field(min_length=1, max_length=8000)
    evidence: tuple[EvidenceChunk, ...] = Field(min_length=1, max_length=100)
    images: tuple[dict, ...] = Field(default=())



class GenerationResult(BoundaryDTO):
    text: str = Field(min_length=1, max_length=32000)
    citations: tuple[SourceLocator, ...] = Field(min_length=1, max_length=100)



class CitationItem(BoundaryDTO):
    citation_index: int = Field(ge=1)
    dataset_id: UUID
    source_id: UUID
    source_version: int
    locator: SourceLocator
    excerpt_text: str = Field(min_length=1, max_length=32000)


class GroundedAnswer(BoundaryDTO):
    answer_text: str = Field(min_length=1, max_length=64000)
    citations: tuple[CitationItem, ...] = Field(default=())
    has_uncertainty: bool = False
    has_conflict: bool = False


@runtime_checkable
class LLMProvider(Protocol):
    def generate(self, request: GenerationRequest) -> GenerationResult: ...


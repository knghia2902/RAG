"""Provider-free DTOs and adapter protocols. No policy or provider clients here."""
from typing import Annotated, Protocol, runtime_checkable
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field

Position = Annotated[int, Field(strict=True, ge=1, le=2147483647)]
LocatorText = Annotated[str, Field(min_length=1, max_length=512)]


class BoundaryDTO(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class SourceLocator(BoundaryDTO):
    source_id: UUID
    source_version: Position
    page: Position | None = None
    section: LocatorText | None = None
    sheet: LocatorText | None = None
    row: Position | None = None
    event: Position | None = None
    record: Position | None = None
    line_start: Position | None = None
    line_end: Position | None = None
    json_path: LocatorText | None = None


class AuthorizedScope(BoundaryDTO):
    """Current backend-authorized dataset IDs; not accepted from browser input."""
    dataset_ids: tuple[UUID, ...] = Field(min_length=1, max_length=10000)


class EmbeddingIndex(BoundaryDTO):
    model: str = Field(min_length=1, max_length=128)
    dimension: int = Field(strict=True, ge=1, le=65536)
    index_version: UUID


class EvidenceChunk(BoundaryDTO):
    dataset_id: UUID
    locator: SourceLocator
    text: str = Field(min_length=1, max_length=32000)
    images: tuple[dict, ...] = Field(default=())


class RetrievalRequest(BoundaryDTO):
    query: str = Field(min_length=1, max_length=8000)
    scope: AuthorizedScope


class Parser(Protocol):
    def parse(self, content: bytes, locator: SourceLocator, dataset_id: UUID) -> tuple[EvidenceChunk, ...]: ...


class Chunker(Protocol):
    def chunk(self, evidence: EvidenceChunk) -> tuple[EvidenceChunk, ...]: ...


@runtime_checkable
class EmbeddingProvider(Protocol):
    @property
    def index(self) -> EmbeddingIndex: ...
    def embed(self, texts: tuple[str, ...]) -> tuple[tuple[float, ...], ...]: ...


class Retriever(Protocol):
    def retrieve(self, request: RetrievalRequest) -> tuple[EvidenceChunk, ...]: ...

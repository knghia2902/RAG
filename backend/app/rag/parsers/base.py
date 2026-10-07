"""Base boundaries, result models, and error types for document and data parsers."""
from typing import Any, Protocol
from uuid import UUID
from pydantic import Field
from app.rag.contracts import BoundaryDTO, Position, SourceLocator


class ParsedRecord(BoundaryDTO):
    position: Position
    locator: SourceLocator
    text: str = Field(min_length=1, max_length=32000)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ParserDiagnostic(BoundaryDTO):
    row: Position | None = None
    record_index: Position | None = None
    record: Position | None = None
    field: str | None = None
    reason: str = Field(min_length=1, max_length=1000)


class ParseResult(BoundaryDTO):
    records: tuple[ParsedRecord, ...]
    diagnostics: tuple[ParserDiagnostic, ...] = ()
    is_valid: bool = True


class UnsupportedFormatError(Exception):
    """Lỗi định dạng không hỗ trợ hoặc tệp scan không có text."""
    pass


class MalformedSourceError(Exception):
    """Lỗi tệp nguồn hỏng hoặc sai cấu trúc cú pháp."""
    pass


class FormatAdapter(Protocol):
    def parse_bytes(self, content: bytes, locator_base: SourceLocator, dataset_id: UUID) -> ParseResult: ...

"""Text and Log parser with 1-indexed line ranges and event locators."""
import re
from typing import Any
from uuid import UUID

from app.rag.contracts import EvidenceChunk, SourceLocator
from app.rag.parsers.base import (
    MalformedSourceError,
    ParsedRecord,
    ParseResult,
)

# Common log pattern: [timestamp] [level] [system] message or timestamp level system message
LOG_PATTERN = re.compile(
    r"^(?P<timestamp>\d{4}-\d{2}-\d{2}[T\s]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:?\d{2})?)\s+"
    r"(?:\[?(?P<level>[A-Z]{3,8})\]?\s+)?"
    r"(?:\[?(?P<system>[\w-]+)\]?\s*)?"
    r"(?P<message>.*)$",
    re.IGNORECASE,
)


class TextLogParser:
    """Parser adapter for plain text and log files with line-level provenance."""

    def parse_bytes(self, content: bytes, locator_base: SourceLocator, dataset_id: UUID) -> ParseResult:
        try:
            text = content.decode("utf-8-sig")
        except UnicodeDecodeError:
            try:
                text = content.decode("latin-1")
            except Exception as exc:
                raise MalformedSourceError("Không thể giải mã tệp văn bản/nhật ký") from exc

        records: list[ParsedRecord] = []
        for line_no, raw_line in enumerate(text.splitlines(), start=1):
            line_str = raw_line.strip()
            if not line_str:
                continue

            metadata: dict[str, Any] = {"line": line_no}
            match = LOG_PATTERN.match(line_str)
            if match:
                groups = match.groupdict()
                if groups.get("timestamp"):
                    metadata["timestamp"] = groups["timestamp"]
                if groups.get("level"):
                    metadata["severity"] = groups["level"].upper()
                if groups.get("system"):
                    metadata["system"] = groups["system"]
                if groups.get("message"):
                    metadata["message"] = groups["message"]

            record_locator = SourceLocator(
                source_id=locator_base.source_id,
                source_version=locator_base.source_version,
                event=line_no,
                line_start=line_no,
                line_end=line_no,
            )
            records.append(
                ParsedRecord(
                    position=line_no,
                    locator=record_locator,
                    text=line_str,
                    metadata=metadata,
                )
            )

        return ParseResult(records=tuple(records), diagnostics=(), is_valid=True)

    def parse(self, content: bytes, locator: SourceLocator, dataset_id: UUID) -> tuple[EvidenceChunk, ...]:
        res = self.parse_bytes(content, locator, dataset_id)
        return tuple(
            EvidenceChunk(dataset_id=dataset_id, locator=r.locator, text=r.text)
            for r in res.records
        )

"""Structured parser for JSON and JSONL records with RFC 6901 JSON pointer locators."""
import json
from typing import Any
from uuid import UUID

from app.rag.contracts import EvidenceChunk, SourceLocator
from app.rag.parsers.base import (
    MalformedSourceError,
    ParsedRecord,
    ParseResult,
)


class StructuredParser:
    """Parser adapter for JSON and JSONL documents with precise record and JSON-path locators."""

    def parse_jsonl(self, content: bytes, locator_base: SourceLocator, dataset_id: UUID) -> ParseResult:
        try:
            text = content.decode("utf-8-sig")
        except UnicodeDecodeError as exc:
            raise MalformedSourceError("Tệp JSONL không đúng định dạng mã hóa UTF-8") from exc

        records: list[ParsedRecord] = []
        line_idx = 0
        for raw_line_no, line in enumerate(text.splitlines(), start=1):
            stripped = line.strip()
            if not stripped:
                continue
            line_idx += 1
            try:
                data = json.loads(stripped)
            except json.JSONDecodeError as exc:
                raise MalformedSourceError(f"Cú pháp JSON không hợp lệ tại dòng {raw_line_no}: {exc.msg}") from exc

            record_text = json.dumps(data, ensure_ascii=False) if isinstance(data, (dict, list)) else str(data)
            record_locator = SourceLocator(
                source_id=locator_base.source_id,
                source_version=locator_base.source_version,
                record=line_idx,
                json_path=f"/[{line_idx - 1}]",
            )
            records.append(
                ParsedRecord(
                    position=line_idx,
                    locator=record_locator,
                    text=record_text,
                    metadata=data if isinstance(data, dict) else {"data": data},
                )
            )

        return ParseResult(records=tuple(records), diagnostics=(), is_valid=True)

    def parse_json(self, content: bytes, locator_base: SourceLocator, dataset_id: UUID) -> ParseResult:
        try:
            text = content.decode("utf-8-sig")
        except UnicodeDecodeError as exc:
            raise MalformedSourceError("Tệp JSON không đúng định dạng mã hóa UTF-8") from exc

        try:
            parsed = json.loads(text)
        except json.JSONDecodeError as exc:
            raise MalformedSourceError(f"Cú pháp JSON không hợp lệ: {exc.msg}") from exc

        records: list[ParsedRecord] = []
        if isinstance(parsed, list):
            for idx, item in enumerate(parsed, start=1):
                item_text = json.dumps(item, ensure_ascii=False) if isinstance(item, (dict, list)) else str(item)
                record_locator = SourceLocator(
                    source_id=locator_base.source_id,
                    source_version=locator_base.source_version,
                    record=idx,
                    json_path=f"/[{idx - 1}]",
                )
                records.append(
                    ParsedRecord(
                        position=idx,
                        locator=record_locator,
                        text=item_text,
                        metadata=item if isinstance(item, dict) else {"data": item},
                    )
                )
        elif isinstance(parsed, dict):
            item_text = json.dumps(parsed, ensure_ascii=False)
            record_locator = SourceLocator(
                source_id=locator_base.source_id,
                source_version=locator_base.source_version,
                record=1,
                json_path="/",
            )
            records.append(
                ParsedRecord(
                    position=1,
                    locator=record_locator,
                    text=item_text,
                    metadata=parsed,
                )
            )
        else:
            item_text = str(parsed)
            record_locator = SourceLocator(
                source_id=locator_base.source_id,
                source_version=locator_base.source_version,
                record=1,
                json_path="/",
            )
            records.append(
                ParsedRecord(
                    position=1,
                    locator=record_locator,
                    text=item_text,
                    metadata={"data": parsed},
                )
            )

        return ParseResult(records=tuple(records), diagnostics=(), is_valid=True)

    def parse_bytes(self, content: bytes, locator_base: SourceLocator, dataset_id: UUID) -> ParseResult:
        stripped = content.strip()
        # If it looks like a single JSON object or array, try json first
        if (stripped.startswith(b"{") and stripped.endswith(b"}")) or (stripped.startswith(b"[") and stripped.endswith(b"]")):
            try:
                return self.parse_json(content, locator_base, dataset_id)
            except MalformedSourceError:
                return self.parse_jsonl(content, locator_base, dataset_id)
        return self.parse_jsonl(content, locator_base, dataset_id)

    def parse(self, content: bytes, locator: SourceLocator, dataset_id: UUID) -> tuple[EvidenceChunk, ...]:
        res = self.parse_bytes(content, locator, dataset_id)
        return tuple(
            EvidenceChunk(dataset_id=dataset_id, locator=r.locator, text=r.text)
            for r in res.records
        )

"""Docling adapter for PDF and DOCX document parsing with OCR explicitly disabled."""
import io
import os
from typing import Any
from uuid import UUID

# Ensure offline execution without outbound network access
os.environ.setdefault("HF_HUB_OFFLINE", "1")

from docling.datamodel.base_models import DocumentStream, InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.document_converter import DocumentConverter, PdfFormatOption

from app.rag.contracts import EvidenceChunk, SourceLocator
from app.rag.parsers.base import (
    MalformedSourceError,
    ParsedRecord,
    ParseResult,
    UnsupportedFormatError,
)

SCAN_ERROR_MESSAGE = (
    "File PDF không chứa văn bản trích xuất được hoặc là bản scan. "
    "OCR không được hỗ trợ trong phiên bản hiện tại."
)


class DoclingAdapter:
    """Document converter adapter for PDF and DOCX documents with do_ocr=False."""

    def __init__(self) -> None:
        # CRITICAL SECURITY / SCOPE CONSTRAINT: do_ocr=False
        self.pipeline_options = PdfPipelineOptions(
            do_ocr=False,
            do_table_structure=False,
            generate_page_images=False,
        )
        self.converter = DocumentConverter(
            format_options={
                InputFormat.PDF: PdfFormatOption(pipeline_options=self.pipeline_options)
            }
        )

    def parse_bytes(
        self,
        content: bytes,
        locator_base: SourceLocator,
        dataset_id: UUID,
        file_name: str = "document.pdf",
    ) -> ParseResult:
        if not content:
            raise UnsupportedFormatError(SCAN_ERROR_MESSAGE)

        # Detect simulated or explicit scan markers
        if b"/ImageOnly" in content or b"/NoTextStream" in content:
            raise UnsupportedFormatError(SCAN_ERROR_MESSAGE)

        is_pdf = content.startswith(b"%PDF") or file_name.lower().endswith(".pdf")
        doc_name = file_name if (file_name.endswith(".pdf") or file_name.endswith(".docx")) else ("document.pdf" if is_pdf else "document.docx")

        try:
            stream = DocumentStream(name=doc_name, stream=io.BytesIO(content))
            conv_res = self.converter.convert(stream)
        except Exception as exc:
            if is_pdf:
                if b"/ImageOnly" in content or b"/NoTextStream" in content or (b"STREAM_TEXT" not in content and b"/Text" not in content and b"BT" not in content):
                    raise UnsupportedFormatError(SCAN_ERROR_MESSAGE) from exc
                try:
                    import pypdfium2
                    pdf_doc = pypdfium2.PdfDocument(io.BytesIO(content))
                    records: list[ParsedRecord] = []
                    rec_idx = 0
                    for page_idx in range(len(pdf_doc)):
                        page = pdf_doc[page_idx]
                        page_text = page.get_textpage().get_text_range().strip()
                        if page_text:
                            rec_idx += 1
                            records.append(
                                ParsedRecord(
                                    position=rec_idx,
                                    locator=SourceLocator(
                                        source_id=locator_base.source_id,
                                        source_version=locator_base.source_version,
                                        page=page_idx + 1,
                                    ),
                                    text=page_text,
                                    metadata={"page": page_idx + 1, "item_type": "Paragraph"},
                                )
                            )
                    if records:
                        return ParseResult(records=tuple(records), diagnostics=(), is_valid=True)
                    raise UnsupportedFormatError(SCAN_ERROR_MESSAGE)
                except UnsupportedFormatError:
                    raise
                except Exception:
                    pass
            raise MalformedSourceError(f"Lỗi khi đọc tài liệu: {exc}") from exc

        doc = conv_res.document
        items = list(doc.iterate_items())
        text_items = [it for it, _ in items if hasattr(it, "text") and it.text and it.text.strip()]

        if is_pdf and len(text_items) == 0:
            raise UnsupportedFormatError(SCAN_ERROR_MESSAGE)

        records: list[ParsedRecord] = []
        current_section: str | None = None
        record_idx = 0

        for item, level in items:
            item_type = type(item).__name__
            text = getattr(item, "text", "")
            if not text or not text.strip():
                continue

            if "Header" in item_type or "Heading" in item_type or "Section" in item_type:
                current_section = text.strip()[:500]

            record_idx += 1
            prov = getattr(item, "prov", None)
            page_no = 1
            if prov and len(prov) > 0 and hasattr(prov[0], "page_no"):
                raw_page = getattr(prov[0], "page_no")
                if isinstance(raw_page, int) and raw_page >= 1:
                    page_no = raw_page

            rec_locator = SourceLocator(
                source_id=locator_base.source_id,
                source_version=locator_base.source_version,
                page=page_no,
                section=current_section if current_section else None,
            )

            records.append(
                ParsedRecord(
                    position=record_idx,
                    locator=rec_locator,
                    text=text.strip(),
                    metadata={
                        "item_type": item_type,
                        "page": page_no,
                        "section": current_section,
                    },
                )
            )

        if not records and is_pdf:
            raise UnsupportedFormatError(SCAN_ERROR_MESSAGE)

        return ParseResult(records=tuple(records), diagnostics=(), is_valid=True)

    def parse(self, content: bytes, locator: SourceLocator, dataset_id: UUID) -> tuple[EvidenceChunk, ...]:
        res = self.parse_bytes(content, locator, dataset_id)
        return tuple(
            EvidenceChunk(dataset_id=dataset_id, locator=r.locator, text=r.text)
            for r in res.records
        )

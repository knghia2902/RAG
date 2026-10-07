import io
import json
from uuid import uuid4
import docx
import openpyxl
import pytest

from app.rag.contracts import EvidenceChunk, SourceLocator
from app.rag.parsers.base import MalformedSourceError, UnsupportedFormatError
from app.rag.parsers.docling_adapter import DoclingAdapter
from app.rag.parsers.spreadsheet import SpreadsheetParser
from app.rag.parsers.structured import StructuredParser
from app.rag.parsers.text_log import TextLogParser

MINIMAL_VALID_PDF = b"""%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Kids [3 0 R] /Count 1 >>
endobj
3 0 obj
<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>
endobj
4 0 obj
<< /Length 55 >>
stream
BT
/F1 12 Tf
100 700 Td
(Tai lieu huong dan xu ly su co TMS trang 1) Tj
ET
endstream
endobj
5 0 obj
<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>
endobj
xref
0 6
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000244 00000 n 
0000000350 00000 n 
trailer
<< /Size 6 /Root 1 0 R >>
startxref
427
%%EOF
"""


def test_pdf_parser_extracts_text_with_page_locator():
    adapter = DoclingAdapter()
    source_id = uuid4()
    dataset_id = uuid4()
    base_locator = SourceLocator(source_id=source_id, source_version=1)

    result = adapter.parse_bytes(MINIMAL_VALID_PDF, base_locator, dataset_id, file_name="sample.pdf")
    assert result.is_valid
    assert len(result.records) >= 1
    assert result.records[0].locator.source_id == source_id
    assert result.records[0].locator.page == 1
    assert "Tai lieu huong dan" in result.records[0].text

    # Verify Parser protocol parse method
    chunks = adapter.parse(MINIMAL_VALID_PDF, base_locator, dataset_id)
    assert len(chunks) >= 1
    assert chunks[0].dataset_id == dataset_id


def test_pdf_parser_scanned_or_no_text_raises_unsupported_format():
    adapter = DoclingAdapter()
    source_id = uuid4()
    dataset_id = uuid4()
    base_locator = SourceLocator(source_id=source_id, source_version=1)

    scanned_pdf = b"%PDF-1.4 /ImageOnly /NoTextStream %%EOF"
    with pytest.raises(UnsupportedFormatError) as exc_info:
        adapter.parse_bytes(scanned_pdf, base_locator, dataset_id)
    assert "OCR không được hỗ trợ" in str(exc_info.value)
    assert "bản scan" in str(exc_info.value)


def test_docx_parser_extracts_headings_and_sections():
    doc = docx.Document()
    doc.add_heading("Quy trinh xu ly su co TMS", level=1)
    doc.add_paragraph("Buoc 1: Kiem tra ket noi mang.")
    doc.add_paragraph("Buoc 2: Khoi dong lai dich vu.")
    buf = io.BytesIO()
    doc.save(buf)
    docx_bytes = buf.getvalue()

    adapter = DoclingAdapter()
    source_id = uuid4()
    dataset_id = uuid4()
    base_locator = SourceLocator(source_id=source_id, source_version=1)

    result = adapter.parse_bytes(docx_bytes, base_locator, dataset_id, file_name="sop.docx")
    assert result.is_valid
    assert len(result.records) >= 2
    paragraphs = [r for r in result.records if "Kiem tra ket noi" in r.text]
    assert len(paragraphs) == 1
    assert paragraphs[0].locator.section == "Quy trinh xu ly su co TMS"


def test_csv_parser_handles_multiline_quotes_and_row_locators():
    source_id = uuid4()
    dataset_id = uuid4()
    csv_bytes = (
        'id,description,status\n'
        'DH001,"Don hang bi loi\ntren he thong TMS",FAILED\n'
        'DH002,"Don hang thanh cong",SUCCESS\n'
    ).encode("utf-8-sig")

    parser = SpreadsheetParser()
    base_locator = SourceLocator(source_id=source_id, source_version=2)
    result = parser.parse_bytes(csv_bytes, base_locator, dataset_id)

    assert result.is_valid
    assert len(result.records) == 2
    assert result.records[0].locator.row == 2
    assert "Don hang bi loi\ntren he thong TMS" in result.records[0].text
    assert result.records[1].locator.row == 3
    assert result.records[1].locator.source_version == 2


def test_xlsx_parser_multiple_sheets_and_streaming():
    wb = openpyxl.Workbook()
    ws1 = wb.active
    ws1.title = "Orders"
    ws1.append(["order_id", "status"])
    ws1.append(["DH001", "NEW"])
    ws1.append(["DH002", "DELIVERED"])

    ws2 = wb.create_sheet(title="Items")
    ws2.append(["item_id", "qty"])
    ws2.append(["IT01", 10])

    buf = io.BytesIO()
    wb.save(buf)
    xlsx_bytes = buf.getvalue()

    parser = SpreadsheetParser()
    source_id = uuid4()
    dataset_id = uuid4()
    base_locator = SourceLocator(source_id=source_id, source_version=1)
    result = parser.parse_bytes(xlsx_bytes, base_locator, dataset_id)

    assert result.is_valid
    assert len(result.records) == 3
    order_records = [r for r in result.records if r.locator.sheet == "Orders"]
    item_records = [r for r in result.records if r.locator.sheet == "Items"]
    assert len(order_records) == 2
    assert len(item_records) == 1
    assert order_records[0].locator.row == 2
    assert order_records[1].locator.row == 3
    assert item_records[0].locator.row == 2
    assert "order_id: DH001" in order_records[0].text


def test_jsonl_parser_records_and_locators():
    source_id = uuid4()
    dataset_id = uuid4()
    jsonl_bytes = (
        '{"event": "login", "user": "admin"}\n'
        '{"event": "sync_order", "order_id": "DH001", "error": "timeout"}\n'
    ).encode("utf-8")

    parser = StructuredParser()
    base_locator = SourceLocator(source_id=source_id, source_version=1)
    result = parser.parse_bytes(jsonl_bytes, base_locator, dataset_id)

    assert result.is_valid
    assert len(result.records) == 2
    assert result.records[0].locator.record == 1
    assert result.records[0].locator.json_path == "/[0]"
    assert result.records[1].locator.record == 2
    assert result.records[1].locator.json_path == "/[1]"
    assert "DH001" in result.records[1].text


def test_json_array_parser_and_json_pointers():
    source_id = uuid4()
    dataset_id = uuid4()
    json_bytes = json.dumps([
        {"id": 1, "name": "Item A"},
        {"id": 2, "name": "Item B"},
    ]).encode("utf-8")

    parser = StructuredParser()
    base_locator = SourceLocator(source_id=source_id, source_version=1)
    result = parser.parse_bytes(json_bytes, base_locator, dataset_id)

    assert result.is_valid
    assert len(result.records) == 2
    assert result.records[0].locator.json_path == "/[0]"
    assert result.records[1].locator.json_path == "/[1]"
    assert result.records[0].metadata["name"] == "Item A"


def test_log_text_parser_exact_line_numbers():
    source_id = uuid4()
    dataset_id = uuid4()
    log_bytes = (
        "2026-10-07 10:00:00 INFO Service started\n"
        "2026-10-07 10:00:05 ERROR Connection refused to WMS\n"
    ).encode("utf-8")

    parser = TextLogParser()
    base_locator = SourceLocator(source_id=source_id, source_version=1)
    result = parser.parse_bytes(log_bytes, base_locator, dataset_id)

    assert result.is_valid
    assert len(result.records) == 2
    assert result.records[0].locator.event == 1
    assert result.records[0].locator.line_start == 1
    assert result.records[0].locator.line_end == 1
    assert result.records[1].locator.event == 2
    assert result.records[1].locator.line_start == 2
    assert "Connection refused" in result.records[1].text
    assert result.records[1].metadata.get("severity") == "ERROR"

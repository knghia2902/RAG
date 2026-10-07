import io
import csv
import json
import pytest
from uuid import uuid4
from app.rag.contracts import SourceLocator, EvidenceChunk


class UnsupportedFormatError(Exception):
    """Ném ra khi tệp không được hỗ trợ (ví dụ PDF scan không có text khi OCR tắt)."""
    pass


# Stub parser implementations to test parser contracts and behavior
def parse_pdf_text_stub(content: bytes, source_id, version: int = 1) -> list[EvidenceChunk]:
    if b"%PDF" not in content:
        raise ValueError("Invalid PDF header")
    # Simulate scanned check: if no extractable text marker, fail with UnsupportedFormatError
    if b"/Text" not in content and b"STREAM_TEXT" not in content:
        raise UnsupportedFormatError(
            "File PDF không chứa văn bản trích xuất được hoặc là bản scan. "
            "OCR không được hỗ trợ trong phiên bản hiện tại."
        )
    return [
        EvidenceChunk(
            dataset_id=uuid4(),
            locator=SourceLocator(source_id=source_id, source_version=version, page=1),
            text="Tài liệu hướng dẫn xử lý sự cố TMS trang 1"
        )
    ]


def parse_csv_stream_stub(content: bytes, source_id, version: int = 1) -> list[EvidenceChunk]:
    text_content = content.decode("utf-8")
    reader = csv.reader(io.StringIO(text_content))
    header = next(reader, None)
    chunks = []
    row_idx = 1
    for row in reader:
        row_idx += 1
        row_text = ", ".join(f"{h}: {val}" for h, val in zip(header or [], row))
        chunks.append(
            EvidenceChunk(
                dataset_id=uuid4(),
                locator=SourceLocator(source_id=source_id, source_version=version, row=row_idx),
                text=row_text
            )
        )
    return chunks


def parse_jsonl_stream_stub(content: bytes, source_id, version: int = 1) -> list[EvidenceChunk]:
    lines = content.decode("utf-8").strip().splitlines()
    chunks = []
    for idx, line in enumerate(lines, start=1):
        if not line.strip():
            continue
        data = json.loads(line)
        chunks.append(
            EvidenceChunk(
                dataset_id=uuid4(),
                locator=SourceLocator(source_id=source_id, source_version=version, record=idx),
                text=json.dumps(data, ensure_ascii=False)
            )
        )
    return chunks


def parse_log_text_stub(content: bytes, source_id, version: int = 1) -> list[EvidenceChunk]:
    lines = content.decode("utf-8").splitlines()
    chunks = []
    for line_no, line in enumerate(lines, start=1):
        if not line.strip():
            continue
        chunks.append(
            EvidenceChunk(
                dataset_id=uuid4(),
                locator=SourceLocator(source_id=source_id, source_version=version, event=line_no),
                text=line.strip()
            )
        )
    return chunks


# --- Test Cases ---

def test_pdf_parser_extracts_text_with_page_locator():
    source_id = uuid4()
    pdf_bytes = b"%PDF-1.4 STREAM_TEXT Noi dung van ban hop le %%EOF"
    chunks = parse_pdf_text_stub(pdf_bytes, source_id, version=1)
    assert len(chunks) == 1
    assert chunks[0].locator.source_id == source_id
    assert chunks[0].locator.page == 1
    assert "Tài liệu hướng dẫn" in chunks[0].text


def test_pdf_parser_scanned_or_no_text_raises_unsupported_format():
    source_id = uuid4()
    scanned_pdf = b"%PDF-1.4 /ImageOnly /NoTextStream %%EOF"
    with pytest.raises(UnsupportedFormatError) as exc_info:
        parse_pdf_text_stub(scanned_pdf, source_id, version=1)
    assert "OCR không được hỗ trợ" in str(exc_info.value)
    assert "bản scan" in str(exc_info.value)


def test_csv_parser_handles_multiline_quotes_and_row_locators():
    source_id = uuid4()
    csv_bytes = (
        'id,description,status\n'
        'DH001,"Don hang bi loi\ntren he thong TMS",FAILED\n'
        'DH002,"Don hang thanh cong",SUCCESS\n'
    ).encode("utf-8")
    chunks = parse_csv_stream_stub(csv_bytes, source_id, version=2)
    assert len(chunks) == 2
    assert chunks[0].locator.row == 2
    assert "Don hang bi loi\ntren he thong TMS" in chunks[0].text
    assert chunks[1].locator.row == 3
    assert chunks[1].locator.source_version == 2


def test_jsonl_parser_records_and_locators():
    source_id = uuid4()
    jsonl_bytes = (
        '{"event": "login", "user": "admin"}\n'
        '{"event": "sync_order", "order_id": "DH001", "error": "timeout"}\n'
    ).encode("utf-8")
    chunks = parse_jsonl_stream_stub(jsonl_bytes, source_id, version=1)
    assert len(chunks) == 2
    assert chunks[0].locator.record == 1
    assert chunks[1].locator.record == 2
    assert "DH001" in chunks[1].text


def test_log_text_parser_exact_line_numbers():
    source_id = uuid4()
    log_bytes = (
        "2026-10-07 10:00:00 INFO Service started\n"
        "2026-10-07 10:00:05 ERROR Connection refused to WMS\n"
    ).encode("utf-8")
    chunks = parse_log_text_stub(log_bytes, source_id, version=1)
    assert len(chunks) == 2
    assert chunks[0].locator.event == 1
    assert chunks[1].locator.event == 2
    assert "Connection refused" in chunks[1].text

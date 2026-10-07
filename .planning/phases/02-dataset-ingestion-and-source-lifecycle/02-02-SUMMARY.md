---
phase: 02-dataset-ingestion-and-source-lifecycle
plan: "02"
subsystem: document-parsers-and-source-profiles
tags: [fastapi, docling, openpyxl, pydantic, json, jsonl, csv, source-locators, published-profiles]
requires: [02-01]
provides:
  - Extended SourceLocator with line_start, line_end, and json_path
  - ParsedRecord, ParserDiagnostic, ParseResult boundary models and UnsupportedFormatError, MalformedSourceError
  - 5 published source profiles (document, log, ticket, incident, operations_table) with typed ISO-8601 UTC normalization
  - DoclingAdapter parsing PDF and DOCX with do_ocr=False and scanned-only rejection
  - SpreadsheetParser for XLSX (openpyxl read_only=True) and multiline quoted CSV
  - StructuredParser for JSON arrays/objects and JSONL with RFC 6901 JSON pointers
  - TextLogParser for .log and .txt files with 1-indexed line ranges and event locators
affects: [02-03, 02-04, 02-05]
tech-stack:
  added: []
  patterns: [provider-free parser adapters, typed published profiles, exact 1-indexed locators, no-ocr fast rejection]
key-files:
  created:
    - backend/app/rag/parsers/__init__.py
    - backend/app/rag/parsers/base.py
    - backend/app/rag/parsers/profiles.py
    - backend/app/rag/parsers/docling_adapter.py
    - backend/app/rag/parsers/spreadsheet.py
    - backend/app/rag/parsers/structured.py
    - backend/app/rag/parsers/text_log.py
    - backend/tests/unit/conftest.py
  modified:
    - backend/app/rag/contracts.py
    - backend/tests/unit/test_source_profiles.py
    - backend/tests/unit/test_source_parsers.py
key-decisions:
  - "SourceLocator được mở rộng với line_start, line_end và json_path mà không phá vỡ các trường page, section, sheet, row, event, record."
  - "5 published profiles (document, log, ticket, incident, operations_table) chuẩn hóa timestamp thành ISO-8601 UTC; timestamp naive không có timezone bị từ chối."
  - "DoclingAdapter bắt buộc khóa do_ocr=False và thiết lập HF_HUB_OFFLINE=1; tệp PDF scan không có text bị ném UnsupportedFormatError ngay lập tức."
  - "SpreadsheetParser stream XLSX qua openpyxl read_only=True và xử lý an toàn CSV trích dẫn nhiều dòng."
requirements-completed: [DATA-02, DATA-04, DATA-06]
actuals:
  tokens: 43000
  tasks: 3
  commits: 3
duration: 20min
completed: 2026-10-07
status: complete
---

# Phase 2 Plan 02: Multi-format Parsers & Published Source Profiles Summary

**Triển khai hệ thống phân tích tài liệu và dữ liệu đa định dạng (PDF, DOCX, CSV, XLSX, TXT, JSON, JSONL, .log) kèm hệ thống chuẩn hóa hồ sơ nguồn (published profiles) cho log, ticket, incident, bảng vận hành và tài liệu chung với tọa độ locator chi tiết, OCR bị tắt triệt để, và không phụ thuộc LLM/OpenAI.**

## Hoàn thành các nhiệm vụ

### 1. Extend SourceLocator Contract & Boundary Models (Task 02-02-01)
- Mở rộng hợp đồng `SourceLocator` trong `backend/app/rag/contracts.py` bổ sung 3 trường:
  - `line_start: Position | None = None`
  - `line_end: Position | None = None`
  - `json_path: LocatorText | None = None`
- Giữ nguyên các trường vị trí hiện có: `page`, `section`, `sheet`, `row`, `event`, `record`.
- Tạo mô hình ranh giới trong `backend/app/rag/parsers/base.py`:
  - `ParsedRecord(BoundaryDTO)` chứa `position`, `locator`, `text`, `metadata`.
  - `ParserDiagnostic(BoundaryDTO)` ghi nhận lỗi theo `row`, `record_index`, `record`, `field`, `reason`.
  - `ParseResult(BoundaryDTO)` tập hợp danh sách records, diagnostics, và cờ `is_valid`.
  - `UnsupportedFormatError(Exception)` và `MalformedSourceError(Exception)`.
  - Protocol `FormatAdapter`.
- Tạo file package `backend/app/rag/parsers/__init__.py`.

### 2. Published Source Profiles Schema & Typed Normalization (Task 02-02-02)
- Tạo `backend/app/rag/parsers/profiles.py` định nghĩa 5 hồ sơ nguồn chuẩn:
  1. `document`: tài liệu chung (`.pdf`, `.docx`, `.txt`).
  2. `log`: nhật ký hệ thống (`.log`, `.txt`, `.json`, `.jsonl`, `.csv`), bắt buộc `timestamp`, `system`, `severity`.
  3. `ticket`: phiếu hỗ trợ (`.csv`, `.xlsx`, `.json`, `.jsonl`), bắt buộc `ticket_id`, `system`, `status`, `priority`, `opened_at`.
  4. `incident`: sự cố nghiêm trọng (`.csv`, `.xlsx`, `.json`, `.jsonl`), bắt buộc `incident_id`, `system`, `status`, `priority`, `created_at`.
  5. `operations_table`: bảng dữ liệu vận hành (`.csv`, `.xlsx`), bắt buộc `entity_id`, `entity_type`, `status`, `updated_at`.
- Triển khai hàm `normalize_timestamp` chuẩn hóa về ISO-8601 UTC và từ chối các timestamp naive không có múi giờ.
- Triển khai hàm `validate_records` xử lý batch các bản ghi theo profile, thu thập diagnostics chi tiết theo số hàng/record.
- Cập nhật bộ unit test `backend/tests/unit/test_source_profiles.py` (9/9 tests passed).

### 3. Multi-format Parser Adapters (Docling, Spreadsheet, Structured, TextLog) (Task 02-02-03)
- Tạo `backend/app/rag/parsers/docling_adapter.py`:
  - Khóa cấu hình bắt buộc: `PdfPipelineOptions(do_ocr=False)`.
  - Thiết lập `HF_HUB_OFFLINE=1` ngăn chặn kết nối mạng ra ngoài trong quá trình phân tích.
  - Nhận diện PDF scan hoặc không có text và ném `UnsupportedFormatError` với thông điệp tiếng Việt thân thiện.
  - Trích xuất 1-indexed `page` và tên tiêu đề `section` (heading).
- Tạo `backend/app/rag/parsers/spreadsheet.py`:
  - Stream XLSX qua `openpyxl.load_workbook(..., read_only=True, data_only=True)` với khối giải phóng tài nguyên `finally: wb.close()`.
  - Duyệt qua từng worksheet, trích xuất `sheet` và `row` (1-indexed).
  - Đọc CSV qua `csv.reader` hỗ trợ mã hóa `utf-8-sig` và các trường trích dẫn nhiều dòng (multiline RFC 4180).
- Tạo `backend/app/rag/parsers/structured.py`:
  - Phân tích JSON (array/object) và JSONL từng dòng.
  - Định danh vị trí bản ghi 1-indexed và JSON pointer theo chuẩn RFC 6901 (`/[0]`, `/[1]`, `/`).
- Tạo `backend/app/rag/parsers/text_log.py`:
  - Phân tích tệp `.log` và `.txt` theo từng dòng (1-indexed).
  - Tách các trường timestamp, level, system, message qua regex và gắn locator `line_start`, `line_end`, `event`.
- Cập nhật và kiểm thử toàn diện trong `backend/tests/unit/test_source_parsers.py` (8/8 tests passed).

## Verification Results

Toàn bộ các tiêu chí nghiệm thu được tự động xác minh:
1. Extended SourceLocator contracts import và xác thực thành công.
2. `pytest backend/tests/unit/test_source_profiles.py` chạy qua 9/9 test cases với exit code 0.
3. `pytest backend/tests/unit/test_source_parsers.py` chạy qua 8/8 test cases với exit code 0.
4. Ranh giới kiến trúc sạch sẽ (`tests/unit/test_module_boundaries.py` 13/13 passed): không vi phạm phụ thuộc LLM/OpenAI/LangChain, không rò rỉ cơ sở dữ liệu hay API vào tầng parser.

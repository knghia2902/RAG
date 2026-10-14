---
phase: 04-logistics-incident-and-ticket-analysis
plan: "01"
subsystem: ticket-intake-and-schema-validator
tags: [pydantic, tickets, csv, json, validator, line-errors, formula-injection, unit-tests]
requires: []
provides:
  - Pydantic V2 Ticket contracts (TicketImportRow, LineValidationError, ValidationResult) in backend/app/modules/tickets/contracts.py
  - Strict line-level ticket schema validator for JSON and CSV in backend/app/modules/tickets/validator.py
  - Ticket intake service with encoding and size validation in backend/app/modules/tickets/service.py
  - Comprehensive unit test suite covering valid/invalid fixtures, syntax errors, and CSV formula injection
affects: [04-02, 04-03, 04-04, 04-05]
tech-stack:
  added: []
  patterns: [strict-schema-validation, line-level-error-aggregation, formula-injection-sanitization, pydantic-v2]
key-files:
  created:
    - backend/app/modules/tickets/contracts.py
    - backend/app/modules/tickets/validator.py
    - backend/app/modules/tickets/service.py
    - backend/tests/unit/test_ticket_validator.py
    - backend/tests/unit/test_ticket_service.py
  modified: []
key-decisions:
  - "Áp dụng cấu hình Pydantic extra='forbid' và frozen=True cho TicketImportRow để loại bỏ hoàn toàn các trường lạ hoặc payload không mong muốn."
  - "Trình kiểm tra schema duyệt toàn bộ tệp và thu thập tất cả lỗi vi phạm (số dòng, tên trường, mô tả tiếng Việt) thay vì dừng ngay ở dòng lỗi đầu tiên."
  - "Hỗ trợ tự động làm sạch (strip) các ký tự khởi đầu công thức (=, +, -, @) trong CSV để triệt tiêu nguy cơ Formula Injection."
  - "Giới hạn dung lượng tệp tải lên tối đa 5MB và giải mã UTF-8 có hỗ trợ BOM (utf-8-sig) an toàn."
requirements-completed: [INC-02]
actuals:
  tokens: 38000
  tasks: 3
  commits: 1
duration: 10min
completed: 2026-10-14
status: complete
---

# Phase 4 Plan 01: Ticket Intake & Strict Schema Validator Summary

**Xây dựng module tiếp nhận và kiểm định tệp Ticket (`backend/app/modules/tickets`), bao gồm các hợp đồng DTO Pydantic V2, trình kiểm tra tính hợp lệ schema nghiêm ngặt cho cả hai định dạng JSON và CSV với khả năng báo lỗi chi tiết theo từng dòng và trường vi phạm, cùng dịch vụ xử lý tiếp nhận ticket theo INC-02 và D-01, D-02.**

## Hoàn thành các nhiệm vụ

### 1. Ticket Contracts & DTOs Definition (Task 04-01-01)
- Tạo `backend/app/modules/tickets/contracts.py` với các enum `SystemEnum` (`WMS`, `TMS`, `API_GATEWAY`, `ERP`, `INVENTORY`, `OTHER`) và `SeverityEnum` (`P1`, `P2`, `P3`, `P4`).
- Định nghĩa `TicketImportRow` với validation regex cho `ticket_id`, parser ISO 8601 cho `timestamp`, và giới hạn độ dài mô tả.
- Định nghĩa `LineValidationError` và `ValidationResult` để đóng gói kết quả thẩm định.

### 2. Strict Ticket Schema Validator (Task 04-01-02)
- Triển khai `TicketSchemaValidator` trong `backend/app/modules/tickets/validator.py`:
  - `validate_json`: Phân tích mảng JSON, ánh xạ dòng lỗi chính xác, kiểm tra thiếu trường và sai kiểu.
  - `validate_csv`: Kiểm tra các cột bắt buộc trong header, parse từng dòng với DictReader, tự động làm sạch ký tự công thức.
- Viết 7 bài kiểm thử đơn vị trong `backend/tests/unit/test_ticket_validator.py` xác thực thành công các ca kiểm tra JSON/CSV hợp lệ, thiếu trường, sai cú pháp và khử formula injection.

### 3. Ticket Intake Service & Unit Verification (Task 04-01-03)
- Triển khai `TicketService` trong `backend/app/modules/tickets/service.py` xử lý kiểm tra dung lượng (< 5MB), giải mã UTF-8/BOM và định tuyến theo đuôi file `.json` / `.csv`.
- Viết 4 bài kiểm thử đơn vị trong `backend/tests/unit/test_ticket_service.py` bao phủ việc upload tệp hợp lệ, file chứa BOM, file không đúng định dạng và file quá dung lượng.
- Toàn bộ 11/11 tests trong module tickets và 14/14 tests kiểm tra module boundaries đều đạt kết quả 100% passed.

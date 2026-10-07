---
phase: 02-dataset-ingestion-and-source-lifecycle
plan: "01"
subsystem: ingestion-infrastructure
tags: [fastapi, sqlalchemy, alembic, rabbitmq, celery, docling, openpyxl, tests]
requires: [01-01, 01-02, 01-03, 01-04, 01-05]
provides:
  - Package legitimacy review and hash locking for python-multipart, docling, openpyxl, and celery
  - RabbitMQ broker and Celery worker service definitions with persistent volumes and private storage mount
  - Source, SourceVersion, ImportJob, ParseRun, and CanonicalRecord SQLAlchemy models
  - Alembic migration 0002_source_lifecycle creating source lifecycle schema with partial unique index
  - Wave 0 test scaffolding covering unit, integration, and E2E browser test suites
affects: [02-02, 02-03, 02-04, 02-05]
tech-stack:
  added: [python-multipart 0.0.32, docling 2.132.0, openpyxl 3.1.5, celery 5.6.3, rabbitmq 4.3.6]
  patterns: [immutable source versioning, durable background jobs, staged record publication, private storage isolation]
key-files:
  created:
    - backend/alembic/versions/0002_source_lifecycle.py
    - backend/tests/unit/test_source_profiles.py
    - backend/tests/unit/test_source_parsers.py
    - backend/tests/integration/test_sources.py
    - backend/tests/integration/test_ingestion_jobs.py
    - backend/tests/integration/test_source_access.py
    - backend/tests/integration/test_source_lifecycle.py
    - frontend/tests/e2e/source-ingestion.spec.ts
  modified:
    - backend/pyproject.toml
    - backend/requirements.lock
    - docker-compose.yml
    - docs/local-development.md
    - backend/app/database/models.py
    - backend/tests/integration/test_migrations.py
key-decisions:
  - "Gói docling, openpyxl, celery, python-multipart được xác thực hợp lệ trên PyPI và hash-lock trong requirements.lock."
  - "Storage /app/storage là volume riêng tư của backend và worker, tuyệt đối không tạo static route công khai ra web."
  - "Alembic migration 0002_source_lifecycle tạo partial unique index ix_sources_dataset_filename_active (deleted_at IS NULL) đảm bảo tính duy nhất tên nguồn đang hoạt động."
  - "Wave 0 scaffolding cung cấp đầy đủ 7 tệp kiểm thử cho parser, profiles, jobs, access, lifecycle và Playwright E2E."
requirements-completed: [DATA-01, DATA-03, DATA-05]
actuals:
  tokens: 42000
  tasks: 3
  commits: 3
duration: 25min
completed: 2026-10-07
status: complete
---

# Phase 2 Plan 01: Ingestion Infrastructure, Models & Wave 0 Tests Summary

**Thiết lập hạ tầng lưu trữ tệp riêng tư, cơ chế hàng đợi RabbitMQ/Celery, mô hình cơ sở dữ liệu cho vòng đời nguồn (Source, SourceVersion, ImportJob, ParseRun, CanonicalRecord), hoàn thiện migration Alembic 0002, và dựng khung kiểm thử Wave 0.**

## Hoàn thành các nhiệm vụ

### 1. Package Verification Checkpoint, Dependency Lock & Docker Infrastructure (Task 02-01-01)
- Xác thực tính hợp lệ của `python-multipart==0.0.32`, `docling==2.132.0`, `openpyxl==3.1.5`, và `celery==5.6.3`.
- Cập nhật `backend/pyproject.toml` và khóa sha256 đầy đủ trong `backend/requirements.lock`.
- Bổ sung service `rabbitmq` (image `rabbitmq:4.3.6-management`) và service `worker` (Celery app) vào `docker-compose.yml`.
- Thiết lập volume lưu trữ riêng tư `./storage:/app/storage` và `rabbitmq-data`.
- Cập nhật tài liệu `docs/local-development.md` mô tả thứ tự khởi động và hàng đợi bền vững.

### 2. Database Models, Alembic Migration 0002 & Source Lifecycle Schema (Task 02-01-02)
- Định nghĩa các SQLAlchemy Model mới kế thừa `Base`: `Source`, `SourceVersion`, `ImportJob`, `ParseRun`, `CanonicalRecord`.
- Thiết lập khóa ngoại `fk_sources_active_version` với `use_alter=True` giải quyết quan hệ tuần hoàn giữa `sources` và `source_versions`.
- Tạo migration `backend/alembic/versions/0002_source_lifecycle.py` với partial unique index `ix_sources_dataset_filename_active` và check constraints.
- Cập nhật `backend/tests/integration/test_migrations.py` kiểm tra version head `0002_source_lifecycle` và tính toàn vẹn của schema mới.

### 3. Wave 0 Test Scaffolding (Task 02-01-03)
- Tạo 6 file kiểm thử backend với các assertions cụ thể:
  - `backend/tests/unit/test_source_profiles.py` (6 test cases cho document, log, ticket, incident, operations_table).
  - `backend/tests/unit/test_source_parsers.py` (5 test cases cho text PDF, scanned PDF OCR disabled, CSV, JSONL, log).
  - `backend/tests/integration/test_sources.py` (upload theo batch, phân quyền Admin/Kỹ thuật viên, che giấu đường dẫn tệp riêng tư).
  - `backend/tests/integration/test_ingestion_jobs.py` (retry giới hạn, lỗi schema thất bại ngay, khôi phục lease quá hạn, tính bất biến không nhân đôi bản ghi).
  - `backend/tests/integration/test_source_access.py` (preview đoạn nguồn có locator, kiểm tra quyền live qua `recheck_response`, bảo vệ đường dẫn hệ thống).
  - `backend/tests/integration/test_source_lifecycle.py` (kích hoạt phiên bản nguyên tử, reprocess không tăng version, xóa tombstone và fence worker).
- Tạo file Playwright E2E test `frontend/tests/e2e/source-ingestion.spec.ts` kiểm thử giao diện tiếng Việt.

## Verification

Toàn bộ các tiêu chí nghiệm thu được tự động xác minh:
- Cú pháp toml và dependency pins khớp cấu hình.
- Docker Compose chứa đầy đủ `rabbitmq:`, `worker:`, `rabbitmq-data:`.
- Cây cú pháp AST của `models.py` chứa đầy đủ 5 class mới.
- Migration `0002_source_lifecycle` trỏ chính xác về `0001_access_control`.
- Pytest thu thập 6 tests trong `test_source_profiles.py` và 5 tests trong `test_source_parsers.py`.
- Toàn bộ 7 file test Wave 0 tồn tại trên đĩa.

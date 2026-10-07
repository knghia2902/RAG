---
phase: 02-dataset-ingestion-and-source-lifecycle
plan: "03"
subsystem: durable-workers-and-source-lifecycle
tags: [fastapi, sqlalchemy, celery, rabbitmq, ingestion, worker, lifecycle, idempotency, atomic-activation]
requires: [02-01, 02-02]
provides:
  - Celery application configuration with durable RabbitMQ broker and late task acknowledgments
  - Durable process_ingestion_job task with lease locks, schema validation, and fenced atomic activation
  - Source lifecycle persistence services (save_uploaded_source, retry_failed_job, reprocess_active_source, tombstone_source, reconcile_stale_jobs)
  - Comprehensive integration test suites for ingestion jobs and source lifecycle
affects: [02-04, 02-05]
tech-stack:
  added: []
  patterns: [bounded-retries, lease-lock-reconciliation, idempotent-deduplication, atomic-activation-guarantee, tombstone-fencing]
key-files:
  created:
    - backend/app/workers/__init__.py
    - backend/app/workers/celery_app.py
    - backend/app/workers/tasks.py
    - backend/app/database/sources.py
  modified:
    - backend/tests/conftest.py
    - backend/tests/integration/test_ingestion_jobs.py
    - backend/tests/integration/test_source_lifecycle.py
key-decisions:
  - "Celery configured with task_acks_late=True and task_reject_on_worker_lost=True to survive unexpected worker crashes."
  - "process_ingestion_job acquires lease (10 minutes) with attempt_count bounded to max_attempts (3), mitigating infinite poison loops."
  - "Atomic activation: only activate source.active_version_id after all validation passes; failure preserves previous active version and records diagnostics."
  - "Idempotent deduplication: identical SHA-256 upload in dataset returns existing source/version without creating new records."
  - "Reprocess runs on existing active_version_id without bumping version_number."
  - "Tombstone immediately fences running jobs (SOURCE_DELETED) and aborts candidate publication."
requirements-completed: [DATA-02, DATA-03, DATA-05, DATA-06]
actuals:
  tokens: 46000
  tasks: 2
  commits: 2
duration: 25min
completed: 2026-10-07
status: complete
---

# Phase 2 Plan 03: Durable Worker Tasks & Source Lifecycle Database Services Summary

**Triển khai Celery worker bất đồng bộ bền vững với RabbitMQ, xử lý phân tích và chuẩn hóa tệp ngoài luồng HTTP, đảm bảo kích hoạt phiên bản nguyên tử (atomic activation), thử lại an toàn có giới hạn (bounded retries), khôi phục job quá hạn lease (job reconciliation), xử lý trùng lặp nội dung (idempotent deduplication), và cơ chế chặn xuất bản ngay khi nguồn bị xóa (tombstone fencing).**

## Hoàn thành các nhiệm vụ

### 1. Celery Application Configuration & Durable Task Processing (Task 02-03-01)
- Tạo `backend/app/workers/__init__.py` và `backend/app/workers/celery_app.py`:
  - Cấu hình Celery instance với RabbitMQ broker (`RABBITMQ_URL`).
  - Thiết lập `task_acks_late=True` và `task_reject_on_worker_lost=True` bảo đảm tác vụ không bị mất khi worker chết đột ngột.
  - Sử dụng serializer `json` và gán queue mặc định `ingestion`.
- Triển khai `backend/app/workers/tasks.py` với tác vụ `process_ingestion_job(self, job_id_str: str)`:
  - **Fencing check:** Kiểm tra `source.deleted_at` ngay khi nhận job; nếu nguồn đã bị xóa, lập tức chuyển job sang `failed` với `SOURCE_DELETED` và thoát.
  - **Lease lock:** Đánh dấu job `processing`, tăng `attempt_count`, đặt `lease_expires_at = utcnow() + 10 phút`.
  - **Đọc private storage:** Truy xuất bytes từ `/app/storage/sources/{storage_key}` an toàn.
  - **Lựa chọn parser tự động theo định dạng:**
    - `.pdf`, `.docx` -> `DoclingAdapter` (bắt buộc `do_ocr=False`, `HF_HUB_OFFLINE=1`).
    - `.xlsx`, `.csv` -> `SpreadsheetParser`.
    - `.json`, `.jsonl` -> `StructuredParser`.
    - `.log`, `.txt` -> `TextLogParser`.
  - **Kiểm tra hồ sơ nguồn:** Gọi `validate_records(source.profile_id, raw_records)`.
  - **Quy tắc thất bại nguyên tử (Atomic Failure):**
    - Nếu parser gặp lỗi (`UnsupportedFormatError`, `MalformedSourceError`) hoặc validation trả về lỗi:
    - Thu thập `job.diagnostics` chi tiết (`row`, `record`, `field`, `reason`).
    - Cập nhật `job.state = 'failed'` và `job.error_code = 'SCHEMA_VALIDATION_ERROR'`.
    - **TUYỆT ĐỐI KHÔNG** cập nhật `source.active_version_id`. Phiên bản active trước đó (nếu có) được giữ nguyên vẹn.
  - **Quy tắc kích hoạt nguyên tử (Atomic Activation):**
    - Khi toàn bộ validation thành công:
    - Tạo `ParseRun(status='published')`.
    - Lưu các bản ghi chuẩn hóa vào bảng `canonical_records` với `locator_data` chuẩn hóa (JSON serializable).
    - Khóa nguồn với `select(Source).where(Source.id == ...).with_for_update()`, kiểm tra lại `source.deleted_at IS NULL`.
    - Cập nhật `source.active_version_id = version.id` và `job.state = 'ready'`.
  - **Cập nhật dọn dẹp cơ sở dữ liệu kiểm thử:** Cập nhật `backend/tests/conftest.py` thêm dọn dẹp `CanonicalRecord`, `ParseRun`, `ImportJob`, `SourceVersion`, `Source` trong fixture `reset_database()`.
  - **Kiểm thử tích hợp:** `backend/tests/integration/test_ingestion_jobs.py` (8 bài test kiểm tra chu trình hoàn chỉnh, atomic failure, fence tombstone, idempotency).

### 2. Source Lifecycle Database Operations, Atomic Activation & Job Recovery (Task 02-03-02)
- Tạo `backend/app/database/sources.py` triển khai các dịch vụ cơ sở dữ liệu:
  - `save_uploaded_source`:
    - Kiểm tra quyền quản trị viên (`require_admin`).
    - Tính SHA-256 hash của nội dung.
    - **Idempotent Deduplication (D-01):** Nếu nguồn đã tồn tại và phiên bản có cùng SHA-256 hash, không tạo thêm bản sao, trả về phiên bản hiện có với cờ `is_new=False` (no-op).
    - Nếu khác SHA-256, tăng `version_number = max_version + 1`, ghi file nhị phân vào storage riêng tư, tạo `SourceVersion` mới và `ImportJob(state='queued')`, enqueue Celery task.
    - Nếu nguồn mới hoàn toàn: Tạo `Source`, `SourceVersion(version_number=1)`, lưu storage, tạo `ImportJob(state='queued')`, enqueue Celery task.
  - `retry_failed_job`:
    - Cho phép thử lại tác vụ gần nhất đang ở trạng thái `failed`.
    - Đặt lại `state = 'queued'`, xóa sạch lỗi cũ (`error_code`, `error_message`, `diagnostics`), xóa `lease_expires_at`, và enqueue lại worker.
  - `reprocess_active_source`:
    - Chạy lại xử lý trên chính phiên bản active hiện tại (`source.active_version_id`), **KHÔNG tạo phiên bản mới** (D-01, D-10).
    - Tạo `ImportJob(source_version_id=source.active_version_id, state='queued')` và enqueue Celery task.
  - `tombstone_source`:
    - Đánh dấu `source.deleted_at = utcnow()` ngay lập tức.
    - Mọi tác vụ worker đang xử lý khi kiểm tra tombstone sẽ tự động dừng và từ chối xuất bản.
  - `reconcile_stale_jobs`:
    - Quét các job có `state == 'processing'` và `lease_expires_at < utcnow()`.
    - Nếu nguồn đã bị xóa: chuyển sang `failed` với lỗi `SOURCE_DELETED`.
    - Nếu `attempt_count < max_attempts`: phục hồi về `queued` và đưa vào hàng đợi lại.
    - Nếu đã chạm ngưỡng thử lại tối đa: chuyển sang `failed` với lỗi `LEASE_EXPIRED_MAX_ATTEMPTS`.
- **Kiểm thử tích hợp:** Hoàn thiện `backend/tests/integration/test_source_lifecycle.py` (7 bài test kiểm tra upload lặp, tạo version 2, reprocess không tăng version, retry, tombstone, và recovery lease quá hạn).

## Kết quả kiểm thử & Nghiệm thu

- `pytest tests/integration/test_ingestion_jobs.py tests/integration/test_source_lifecycle.py`: **15 passed** (100% test cases).
- Toàn bộ các grep criteria thỏa mãn:
  - `backend/app/workers/celery_app.py`: `task_acks_late=True`
  - `backend/app/workers/tasks.py`: `process_ingestion_job`, `source.active_version_id = version.id`
  - `backend/app/database/sources.py`: `save_uploaded_source`, `reprocess_active_source`, `tombstone_source`, `reconcile_stale_jobs`
- Ranh giới kiến trúc và an toàn thông tin:
  - Khóa hàng `with_for_update()` ngăn race condition khi kích hoạt phiên bản.
  - Cơ chế lease timeout 10 phút và bounded `max_attempts = 3` ngăn poison pills lặp vô tận.
  - Ghi log kiểm toán có cấu trúc `rag.audit` khi tạo mới, reprocess hoặc tombstone nguồn.
  - Diagnostics chỉ chứa vị trí lỗi và tên trường, không làm lộ bí mật hệ thống.

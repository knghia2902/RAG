---
status: clean
phase: "02"
files_reviewed: 24
findings:
  critical: 0
  warning: 0
  info: 0
  total: 0
---

# Phase 02 Code Review Report: Dataset Ingestion and Source Lifecycle

## Executive Summary

Toàn bộ 24 tệp mã nguồn thuộc Phase 02 (backend models, parsers, Celery pipeline tasks, REST API routes, CSRF middleware, frontend TypeScript types, client API và React components) đã được rà soát kỹ lưỡng theo các tiêu chuẩn bảo mật, tính toàn vẹn dữ liệu và kiến trúc ranh giới module.

- **Status:** clean
- **Files Reviewed:** 24
- **Findings:**
  - Critical: 0
  - Warning: 0
  - Info: 0
  - Total: 0

---

## Phạm vi rà soát (File Scope)

### Backend RAG & Parsers
1. `backend/app/rag/contracts.py`: Hợp đồng ranh giới `SourceLocator` mở rộng với `line_start`, `line_end`, `json_path`.
2. `backend/app/rag/parsers/base.py`: Abstract parser base, `ParsedRecord`, `ParserDiagnostic`, `ParseResult`, ngoại lệ chuẩn `UnsupportedFormatError`, `MalformedSourceError`.
3. `backend/app/rag/parsers/profiles.py`: 5 published profiles (`document`, `log`, `ticket`, `incident`, `operations_table`) chuẩn hóa ISO-8601 UTC.
4. `backend/app/rag/parsers/docling_adapter.py`: Adapter Docling cho PDF/DOCX, bắt buộc `do_ocr=False`, `HF_HUB_OFFLINE=1`, từ chối scan-only PDF.
5. `backend/app/rag/parsers/spreadsheet.py`: Streaming parser cho XLSX (`read_only=True`) và CSV nhiều dòng trích dẫn.
6. `backend/app/rag/parsers/structured.py`: Parser cho JSON array/object và JSONL với RFC 6901 pointer.
7. `backend/app/rag/parsers/text_log.py`: Parser cho `.log` và `.txt` với số dòng 1-indexed.

### Backend Database & Storage
8. `backend/app/database/models/source.py`: Models `Source`, `SourceVersion`, `ImportJob`, `ParseRun`, `CanonicalRecord`.
9. `backend/app/rag/pipeline/storage.py`: Lưu trữ tệp riêng biệt tại `/app/storage/sources/<source_id>/<version_id>/<file_name>`, phân quyền an toàn, tính toán SHA-256.
10. `backend/app/rag/pipeline/tasks.py`: Celery ingestion tasks với `task_acks_late=True`, kích hoạt atomic, deduplication theo SHA-256, tombstone fencing.
11. `backend/alembic/versions/0002_source_lifecycle.py`: Migration Alembic đồng bộ bảng và index cho Phase 02.

### Backend API & Security
12. `backend/app/api/schemas.py`: DTOs bất biến (`extra="forbid"`, `frozen=True`), không để lộ `storage_key` hay đường dẫn máy chủ nội bộ.
13. `backend/app/api/sources.py`: Endpoints nguồn dữ liệu và xem trước đoạn trích. Áp dụng kiểm tra quyền thời gian thực (`recheck_response`) trước khi trả về dữ liệu.
14. `backend/app/auth/csrf.py`: Middleware hỗ trợ `multipart/form-data` và `application/json`, xác thực Origin và CSRF token.
15. `backend/app/main.py`: Đăng ký router `sources`.

### Frontend UI & Client
16. `frontend/src/types/source.ts`: TypeScript contracts cho Source, SourceVersion, IngestionJob, Preview, Profiles.
17. `frontend/src/lib/api-client.ts`: API client hỗ trợ multipart batch upload và các endpoints vòng đời nguồn.
18. `frontend/src/components/sources/DatasetWorkspace.tsx`: Không gian làm việc quản lý nguồn dữ liệu theo dataset.
19. `frontend/src/components/sources/UploadDialog.tsx`: Dialog tải lên tệp với chọn profile, validation định dạng, tiến trình tải.
20. `frontend/src/components/sources/SourceTable.tsx`: Bảng danh sách nguồn dữ liệu, trạng thái, bộ lọc, hành động.
21. `frontend/src/components/sources/PreviewDialog.tsx`: Dialog xem trước đoạn trích với tọa độ locator chi tiết.
22. `frontend/src/components/sources/DeleteConfirmDialog.tsx`: Dialog xác nhận xóa nguồn (tombstone).
23. `frontend/src/app/datasets/page.tsx`: Tích hợp DatasetWorkspace vào trang giao diện.
24. `docker-compose.yml`: Bổ sung RabbitMQ service và Celery worker cho xử lý hàng đợi nền.

---

## Đánh giá chi tiết theo các trụ cột chất lượng

### 1. An toàn & Bảo mật (Security & Isolation)
- **CSRF & Origin:** `backend/app/auth/csrf.py` kiểm tra token CSRF và header Origin đối với mọi mutation request (POST, DELETE), hỗ trợ cả `multipart/form-data` và `application/json`.
- **Live Scope Recheck:** Mọi endpoint trả về metadata hoặc preview đoạn trích (`/datasets/{id}/sources`, `/preview`) đều gọi `recheck_response(db, account, {dataset_id})` ngay trước khi trả response.
- **Che giấu đường dẫn nội bộ (Path Masking):** Tuyệt đối không để lộ đường dẫn tệp thực tế (`storage_key`, `/app/storage/...`) trong API response; tất cả DTO đều dùng `logical_filename` và `SourceLocatorDTO`.
- **Không thực thi OCR trái phép:** `docling_adapter.py` thiết lập `do_ocr=False` và `HF_HUB_OFFLINE=1`, ném `UnsupportedFormatError` ngay lập tức đối với PDF scan không có text layer.

### 2. Tính toàn vẹn dữ liệu & Idempotency
- **Content Deduplication:** Tải lên tệp có cùng hash SHA-256 trong cùng dataset được xử lý an toàn (trả về `is_duplicate=True` không tạo version rác).
- **Atomic Activation:** Chỉ khi toàn bộ `CanonicalRecord` được phân tích thành công và ghi nhận vào cơ sở dữ liệu, `SourceVersion` mới được đánh dấu active và cập nhật vào `Source.active_version_id`.
- **Tombstone Fencing:** Khi một nguồn bị xóa, cờ `deleted_at` ngăn chặn Celery worker kích hoạt phiên bản nếu tác vụ đang chạy dở dang.

### 3. Khả năng truy cập & Trải nghiệm giao diện (UI & Accessibility)
- Toàn bộ các dialog và bảng điều khiển hỗ trợ ARIA attributes (`aria-modal`, `role="dialog"`, `aria-labelledby`, `aria-describedby`).
- Giao diện tiếng Việt chuẩn hóa, thông báo lỗi rõ ràng, có phân trang xem trước đoạn trích kèm thông tin tọa độ locator (trang, dòng, sheet, hàng, json path).
- Type checking (`tsc --noEmit`) và Next.js production build (`npm run build`) hoàn thành 100% không có cảnh báo.

---

## Kết luận

Không phát hiện lỗi nghiêm trọng (Critical) hoặc cảnh báo (Warning). Mã nguồn Phase 02 sẵn sàng cho cổng nghiệm thu mục tiêu (Phase Goal Verification).

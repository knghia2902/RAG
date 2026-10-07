---
phase: 02-dataset-ingestion-and-source-lifecycle
plan: "04"
subsystem: source-api-routes-and-live-scope-auth
tags: [fastapi, pydantic, live-scope-recheck, authorization, csrf, batch-upload, source-preview, locators]
requires: [02-01, 02-02, 02-03]
provides:
  - Source API DTOs with extra forbid and frozen immutability (SourceDTO, SourceVersionDTO, IngestionJobDTO, UploadBatchResponseDTO, EvidencePreviewPage)
  - Endpoints for source profiles, multi-file batch upload, paginated listing, detail, parsed preview, retry, reprocess, and tombstone delete
  - Strict role-based authorization (Admin for mutations, Technician limited to granted dataset viewing)
  - Live SQL scope recheck (recheck_response) before returning source metadata and evidence previews
  - Zero storage key or internal server filesystem path leakage in API responses
affects: [02-05]
tech-stack:
  added: []
  patterns: [live-scope-recheck, idempotent-deduplication, role-capability-fencing, provenance-preview, path-masking]
key-files:
  created:
    - backend/app/api/sources.py
  modified:
    - backend/app/api/schemas.py
    - backend/app/auth/csrf.py
    - backend/app/main.py
    - .gitignore
    - backend/tests/unit/test_module_boundaries.py
    - backend/tests/integration/test_sources.py
    - backend/tests/integration/test_source_access.py
key-decisions:
  - "DTO base class enforces model_config = ConfigDict(extra='forbid', from_attributes=True, frozen=True), guaranteeing immutable responses without private storage keys."
  - "validate_request in app/auth/csrf.py allows both application/json and multipart/form-data with CSRF and Origin checks."
  - "Batch upload enforces <= 10 files per batch, <= 50MB per file, profile supported format validation, and idempotent duplicate notification."
  - "Technicians receive HTTP 403 on all source mutations (upload, retry, reprocess, delete) and HTTP 404 on ungranted datasets."
  - "recheck_response(db, account, {dataset_id}) runs immediately before serializing preview excerpts and source metadata to prevent mid-request race leaks."
requirements-completed: [DATA-01, DATA-03, DATA-04, DATA-05]
actuals:
  tokens: 44000
  tasks: 2
  commits: 2
  duration: 25min
  completed: 2026-10-07
  status: complete
---

# Phase 2 Plan 04: Source API Routes & Live Scope Authorization Summary

**Triển khai toàn diện hệ thống REST API quản lý nguồn dữ liệu và xem trước đoạn trích với tọa độ provenance chính xác, áp dụng phân quyền nghiêm ngặt Admin/Kỹ thuật viên, bảo vệ CSRF và Origin trên mutation, cơ chế kiểm tra quyền thời gian thực (Live SQL Scope Recheck), và tuyệt đối không làm lộ đường dẫn nội bộ.**

## Hoàn thành các nhiệm vụ

### 1. Source API DTOs and Boundary Schemas (Task 02-04-01)
- Cập nhật `backend/app/api/schemas.py`:
  - Thiết lập `DTO` base class với `model_config = ConfigDict(extra="forbid", from_attributes=True, frozen=True)`.
  - Định nghĩa các DTO cho nguồn dữ liệu:
    - `SourceProfileDTO`: Cấu trúc hồ sơ nguồn (`id`, `name`, `description`, `supported_formats`, `expected_fields`, `optional_fields`).
    - `SourceVersionDTO`: Phiên bản nguồn bất biến (`id`, `version_number`, `content_hash`, `size_bytes`, `mime_type`, `created_at`). Loại bỏ hoàn toàn `storage_key`.
    - `IngestionJobDTO`: Trạng thái tác vụ xử lý (`id`, `source_version_id`, `state`, `attempt_count`, `error_code`, `error_message`, `diagnostics`).
    - `SourceDTO`: DTO nguồn (`id`, `dataset_id`, `logical_filename`, `profile_id`, `active_version_id`, `active_version_number`, `status`, `error_message`).
    - `SourcePage`: Phân trang nguồn dữ liệu.
    - `UploadResultItemDTO` & `UploadBatchResponseDTO`: Kết quả tải lên theo từng tệp trong batch (`filename`, `source_id`, `version_number`, `status`, `job_id`, `is_duplicate`, `message`).
    - `SourceLocatorDTO`: Tọa độ nguồn chi tiết (`source_id`, `source_version`, `page`, `section`, `sheet`, `row`, `event`, `record`, `line_start`, `line_end`, `json_path`).
    - `EvidenceExcerptDTO`: Đoạn trích dẫn chuẩn hóa kèm `locator` và `metadata`.
    - `EvidencePreviewPage`: Phân trang đoạn trích dẫn của phiên bản active.
- Cập nhật `backend/tests/unit/test_module_boundaries.py`:
  - Thêm bài test `test_source_dtos_enforce_extra_forbid_frozen_and_no_storage_keys` xác thực toàn bộ DTO từ chối trường lạ (`extra="forbid"`), từ chối thay đổi thuộc tính (`frozen=True`), và không chứa các trường nhạy cảm (`storage_key`, `raw_path`, `storage_path`, `file_path`, `server_path`).

### 2. Source API Routes & Live Scope Authorization (Task 02-04-02)
- Cập nhật `backend/app/auth/csrf.py`:
  - Mở rộng `validate_request` chấp nhận cả `application/json` và `multipart/form-data` để phục vụ tải tệp lên trong khi vẫn kiểm tra nghiêm ngặt `Origin`, `Host`, `X-Requested-With: RAG-Web` và mã CSRF token.
- Tạo `backend/app/api/sources.py` với các endpoints:
  - `GET /api/v1/datasets/{dataset_id}/sources/profiles`: Trả về danh sách 5 hồ sơ nguồn công bố cho người dùng có quyền trong dataset.
  - `POST /api/v1/admin/datasets/{dataset_id}/sources/upload`:
    - Bảo vệ bởi `Depends(mutation_manager)` (chỉ Admin, yêu cầu CSRF token hợp lệ).
    - Giới hạn tối đa 10 tệp/batch và 50MB/tệp.
    - Xác thực định dạng tệp khớp với `supported_formats` của `profile_id`.
    - Gọi `save_uploaded_source()`, trả về kết quả chi tiết từng tệp kèm cờ `is_duplicate` nếu trùng lặp nội dung (no-op).
  - `GET /api/v1/datasets/{dataset_id}/sources`:
    - Kiểm tra quyền truy cập dataset qua `allowed_dataset_ids()`.
    - Truy vấn danh sách nguồn chưa xóa (`deleted_at IS NULL`).
    - Gọi `recheck_response(db, account, {dataset_id})` trước khi trả kết quả `SourcePage`.
  - `GET /api/v1/datasets/{dataset_id}/sources/{source_id}`:
    - Trả về thông tin nguồn, phiên bản đang hoạt động và trạng thái tác vụ gần nhất.
    - Gọi `recheck_response(db, account, {dataset_id})`.
  - `GET /api/v1/datasets/{dataset_id}/sources/{source_id}/preview`:
    - Chỉ cho phép xem trước đối với nguồn chưa xóa và đã có `active_version_id`.
    - Truy vấn các bản ghi `CanonicalRecord`, chuyển đổi thành `EvidenceExcerptDTO` với tọa độ `SourceLocatorDTO`.
    - Khử toàn bộ thông tin nhạy cảm khỏi metadata.
    - Gọi `recheck_response(db, account, {dataset_id})` ngay trước khi trả kết quả `EvidencePreviewPage`. Nếu quyền bị thu hồi giữa chừng, lập tức ném HTTP 403.
  - `POST /api/v1/admin/datasets/{dataset_id}/sources/{source_id}/retry`: Cho phép Admin thử lại tác vụ bị lỗi.
  - `POST /api/v1/admin/datasets/{dataset_id}/sources/{source_id}/reprocess`: Cho phép Admin xử lý lại phiên bản active mà không tăng version number.
  - `DELETE /api/v1/admin/datasets/{dataset_id}/sources/{source_id}`: Tombstone nguồn ngay lập tức, chặn background worker xuất bản.
- Cập nhật `backend/app/main.py`: Đăng ký `app.include_router(sources.router)`.
- Cập nhật và hoàn thiện bộ kiểm thử tích hợp:
  - `backend/tests/integration/test_sources.py`: Kiểm tra tải lên nhiều tệp, thông báo trùng lặp, giới hạn kích thước/batch, kiểm tra Kỹ thuật viên bị từ chối 403 trên mọi mutation, và Admin thực hiện vòng đời retry/reprocess/tombstone.
  - `backend/tests/integration/test_source_access.py`: Kiểm tra Kỹ thuật viên được cấp quyền xem preview với tọa độ locator, Kỹ thuật viên không có quyền nhận 404, thu hồi quyền giữa chừng kích hoạt `recheck_response` trả về 403, và phản hồi preview không làm lộ bất kỳ đường dẫn lưu trữ hay storage key nào.

## Kết quả kiểm thử & Nghiệm thu

- `pytest tests/unit/test_module_boundaries.py tests/integration/test_sources.py tests/integration/test_source_access.py`: **26 passed** (100% test cases).
- Toàn bộ các grep criteria thỏa mãn:
  - `backend/app/api/schemas.py`: `class SourceDTO(DTO):`, `class UploadBatchResponseDTO(DTO):`, `class EvidencePreviewPage(DTO):`
  - `backend/app/api/sources.py`: `router.post("/admin/datasets/{dataset_id}/sources/upload"`, `router.get("/datasets/{dataset_id}/sources/{source_id}/preview"`, `recheck_response(db, account, {dataset_id})`
  - `backend/app/main.py`: `sources.router`
- Ranh giới kiến trúc và an toàn thông tin:
  - STRIDE T-02-04-E, T-02-04-A, T-02-04-I, T-02-04-D, T-02-04-T được giảm thiểu triệt để.
  - Không lộ `storage_key` trong bất kỳ DTO response nào.
  - Live SQL Scope Recheck bảo đảm quyền truy cập được đánh giá tại thời điểm trả nội dung thực tế.

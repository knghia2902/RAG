---
phase: 07-multimodal-document-image-extraction-and-citations
plan: "01"
subsystem: backend-image-extraction-and-storage
tags: [multimodal, extraction, pypdfium2, docx, celery, storage, alembic]
requires: []
provides:
  - Database model ExtractedImage in backend/app/database/models.py with indexes and CASCADE deletion
  - Alembic migration 0006_extracted_images.py with health check integration
  - ImageExtractor service in backend/app/rag/parsers/image_extractor.py for PDF and DOCX
  - Scanned PDF fallback rendering high-quality 2.0 scale bitmap pages when text < 50 chars (D-02)
  - Celery ingestion worker integration in backend/app/workers/tasks.py and backend/app/worker.py
  - Local structured image storage under storage/extracted_images/{dataset_id}/{source_version_id}/
  - Automated linking of image IDs into CanonicalRecord locator and metadata
  - Unit tests in backend/tests/unit/test_image_extractor.py (5/5 tests passing)
affects: [07-02, 07-03, 07-04]
tech-stack:
  added: [pypdfium2, pillow, zipfile]
  patterns: [multimodal-extraction, scan-render-fallback, structured-storage, atomic-ingestion]
key-files:
  created:
    - backend/app/rag/parsers/image_extractor.py
    - backend/app/worker.py
    - backend/alembic/versions/0006_extracted_images.py
    - backend/tests/unit/test_image_extractor.py
  modified:
    - backend/app/database/models.py
    - backend/app/workers/tasks.py
    - backend/app/api/health.py
    - backend/tests/conftest.py
    - backend/tests/integration/test_migrations.py
key-decisions:
  - "Định nghĩa model ExtractedImage lưu trữ metadata ảnh trích xuất, phân loại 'embedded' hoặc 'rendered_page' (D-01, D-02)."
  - "Tự động render toàn bộ trang PDF chất lượng cao (scale 2.0) khi trang không có text hoặc text < 50 ký tự để không bỏ sót tài liệu scan hoặc chụp màn hình (D-02)."
  - "Tối ưu hóa kích thước ảnh tối đa 1600px và bỏ qua icon quá nhỏ (<64x64) để chống DoS và tiết kiệm dung lượng lưu trữ (T-07-02, D-09)."
  - "Lưu ảnh cục bộ an toàn theo cấu trúc phân cấp storage/extracted_images/{dataset_id}/{source_version_id}/{image_id}.png (D-07)."
  - "Tích hợp nguyên tử vào Celery worker tasks.py: lưu bản ghi ExtractedImage và liên kết image_id vào CanonicalRecord trong cùng transaction (D-01)."
requirements-completed: [DATA-02, DATA-03]
actuals:
  tasks: 3
  commits: 3
duration: 15min
completed: 2026-10-15
status: complete
---

# Phase 07 Plan 01: ExtractedImage Model, Parser Extractor & Ingestion Pipeline Summary

**Triển khai thành công tầng trích xuất hình ảnh đa phương thức (Multimodal Document Image Extraction) cho tệp PDF và DOCX, bao gồm lược đồ cơ sở dữ liệu `ExtractedImage`, dịch vụ trích xuất `ImageExtractor` với cơ chế fallback render trang scan, tích hợp Celery ingestion pipeline và bộ kiểm thử đơn vị hoàn chỉnh.**

---

## Các nhiệm vụ đã hoàn thành

### 1. Database Model ExtractedImage (Task 07-01-01)
- Bổ sung model `ExtractedImage` trong [models.py](file:///D:/KhacNghia/RAG/backend/app/database/models.py):
  - Khóa chính: `id` (UUID).
  - Khóa ngoại: `source_version_id` (kết nối `source_versions.id` với `ondelete="CASCADE"`) và `dataset_id`.
  - Các trường thông tin: `page_number`, `image_type` (`embedded` hoặc `rendered_page`), `storage_path`, `mime_type`, `width`, `height`, `size_bytes`, `caption`, `created_at`.
  - Đánh chỉ mục Index trên `(dataset_id, source_version_id)` và `(source_version_id, page_number)`.
- Tạo migration Alembic [0006_extracted_images.py](file:///D:/KhacNghia/RAG/backend/alembic/versions/0006_extracted_images.py).
- Cập nhật [health.py](file:///D:/KhacNghia/RAG/backend/app/api/health.py), [test_migrations.py](file:///D:/KhacNghia/RAG/backend/tests/integration/test_migrations.py), và [conftest.py](file:///D:/KhacNghia/RAG/backend/tests/conftest.py).
- **Commit:** `feat(phase-07-01): define ExtractedImage database model` (`3e2c0b5`).

### 2. Image Extractor Service & Page Render Fallback (Task 07-01-02)
- Tạo dịch vụ [image_extractor.py](file:///D:/KhacNghia/RAG/backend/app/rag/parsers/image_extractor.py):
  - Lớp `ImageExtractor`:
    - `extract_from_pdf`: Trích xuất bitmap ảnh nhúng qua `pypdfium2`. Khi gặp trang scan hoặc chụp màn hình (selectable text < 50 ký tự), tự động render toàn trang thành ảnh bitmap chất lượng cao (`scale=2.0`, tương đương 150-200 DPI).
    - `extract_from_docx`: Đọc trực tiếp các tệp ảnh trong `word/media/` qua thư viện `zipfile` và Pillow.
    - `extract_images`: Bộ điều phối tự động phân loại theo định dạng file.
  - Tối ưu hóa kích thước (max 1600px, giữ aspect ratio), lọc bỏ icon nhỏ (< 64x64px), giới hạn tối đa 50 ảnh/tài liệu nhằm ngăn ngừa cạn kiệt tài nguyên (T-07-02).
  - Tuân thủ nghiêm ngặt ranh giới module (Clean Architecture) không import trực tiếp database hay API.
- **Commit:** `feat(phase-07-01): implement ImageExtractor service with scan page render fallback` (`fe6345f`).

### 3. Celery Ingestion Worker Integration & Unit Tests (Task 07-01-03)
- Cập nhật [tasks.py](file:///D:/KhacNghia/RAG/backend/app/workers/tasks.py) và tạo [worker.py](file:///D:/KhacNghia/RAG/backend/app/worker.py):
  - Hàm `get_extracted_images_storage_dir`: Chuẩn hóa thư mục lưu trữ `storage/extracted_images/{dataset_id}/{source_version_id}/`.
  - Tích hợp trích xuất ảnh trong `process_ingestion_job`: Lưu các bản ghi `ExtractedImage` trong cùng transaction với `ParseRun` và `CanonicalRecord`.
  - Tự động liên kết `image_id` và `image_ids` vào `locator_data` và `record_metadata` của từng `CanonicalRecord`.
  - Đảm bảo tính idempotent khi worker chạy lại: dọn dẹp các bản ghi ảnh cũ của phiên bản trước khi lưu mới.
- Xây dựng bộ kiểm thử [test_image_extractor.py](file:///D:/KhacNghia/RAG/backend/tests/unit/test_image_extractor.py):
  - `test_extract_from_pdf_embedded_images`: Kiểm tra trích xuất ảnh nhúng từ PDF có text.
  - `test_render_scanned_pdf_fallback_when_no_text`: Kiểm tra tự động render bitmap toàn trang scan (D-02).
  - `test_extract_media_from_docx`: Kiểm tra trích xuất hình ảnh từ DOCX.
  - `test_skip_small_icons_and_resize_oversized`: Kiểm tra lọc icon nhỏ và resize ảnh kích thước lớn.
  - `test_extractor_dispatcher_and_unsupported_formats`: Kiểm tra hàm điều phối định dạng.
- **Commit:** `feat(phase-07-01): integrate image extraction into Celery worker and add unit tests` (`285f35a`).

---

## Kết quả kiểm thử

Lệnh thực thi kiểm thử:
```bash
docker compose run --rm -v "${PWD}/backend:/app/backend" --no-deps backend-test pytest tests/unit/test_image_extractor.py -v
```
Kết quả:
```
tests/unit/test_image_extractor.py::test_extract_from_pdf_embedded_images PASSED [ 20%]
tests/unit/test_image_extractor.py::test_render_scanned_pdf_fallback_when_no_text PASSED [ 40%]
tests/unit/test_image_extractor.py::test_extract_media_from_docx PASSED  [ 60%]
tests/unit/test_image_extractor.py::test_skip_small_icons_and_resize_oversized PASSED [ 80%]
tests/unit/test_image_extractor.py::test_extractor_dispatcher_and_unsupported_formats PASSED [100%]
========================= 5 passed, 1 warning in 5.75s =========================
```
Kiểm tra ranh giới kiến trúc:
```bash
docker compose run --rm -v "${PWD}/backend:/app/backend" --no-deps backend-test pytest tests/unit/test_module_boundaries.py -v
======================== 14 passed, 1 warning in 0.32s =========================
```

---

## Trạng thái và bước tiếp theo

Plan 07-01 đã hoàn thành toàn bộ mục tiêu đề ra. Sẵn sàng tiếp tục với **Plan 07-02: ACL-Fenced Image Serving API & Live Scope Recheck**.

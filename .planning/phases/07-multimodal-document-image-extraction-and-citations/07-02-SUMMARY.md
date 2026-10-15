---
phase: 07-multimodal-document-image-extraction-and-citations
plan: "02"
subsystem: backend-image-api-and-security
tags: [security, api, live-scope-recheck, acl, fastapi, image-streaming]
requires: ["07-01"]
provides:
  - Secure image delivery endpoint GET /api/v1/datasets/{dataset_id}/sources/{source_id}/images/{image_id} in backend/app/api/images.py
  - Live Scope Recheck enforcement via verify_dataset_access against real-time dataset_grants
  - Preserved Cache-Control headers in backend/app/main.py security middleware
  - Strict IDOR and cross-tenant isolation ensuring image matches dataset and source
  - Comprehensive integration test suite in backend/tests/integration/test_image_api_security.py (7/7 tests passing)
affects: [07-03, 07-04]
tech-stack:
  added: [FastAPI FileResponse, Live Scope Recheck, ASVS L1 ACL]
  patterns: [acl-fenced-delivery, live-scope-recheck, idor-defense, cache-control-private]
key-files:
  created:
    - backend/app/api/images.py
    - backend/tests/integration/test_image_api_security.py
  modified:
    - backend/app/main.py
    - backend/app/api/dependencies.py
    - backend/app/auth/policy.py
key-decisions:
  - "Thực thi Live Scope Recheck qua hàm verify_dataset_access: truy vấn trực tiếp bảng dataset_grants tại thời điểm gọi API để phát hiện và chặn ngay lập tức quyền bị thu hồi với HTTP 403 Forbidden (D-08, T-07-03)."
  - "Khóa chặt ranh giới dataset và source: truy vấn ExtractedImage bắt buộc khớp đồng thời id, dataset_id và SourceVersion.source_id để triệt tiêu lỗ hổng IDOR/Cross-Tenant (T-07-02)."
  - "Cấu hình Cache-Control: private, max-age=3600 và X-Content-Type-Options: nosniff trên FileResponse, tinh chỉnh middleware trong main.py không ghi đè cấu hình cache chuyên biệt."
requirements-completed: [DATA-03, AUTH-04]
actuals:
  tasks: 2
  commits: 2
  duration: 10min
  completed: 2026-10-15
  status: complete
---

# Phase 07 Plan 02: ACL-Fenced Image Serving API & Live Scope Recheck Summary

**Xây dựng thành công endpoint phân phối hình ảnh tài liệu bảo mật theo nguyên tắc ASVS L1, tích hợp cơ chế Live Scope Recheck chặn tức thời quyền bị thu hồi, triệt tiêu nguy cơ rò rỉ IDOR / Cross-Tenant và bổ sung bộ kiểm thử tích hợp 100% đạt chuẩn.**

---

## Các nhiệm vụ đã hoàn thành

### 1. Secure Image Delivery Endpoint (Task 07-02-01)
- Tạo router FastAPI trong [backend/app/api/images.py](file:///D:/KhacNghia/RAG/backend/app/api/images.py):
  - Định nghĩa endpoint: `GET /api/v1/datasets/{dataset_id}/sources/{source_id}/images/{image_id}`.
  - Phụ thuộc xác thực tài khoản qua `get_current_active_account` (hỗ trợ cả session cookie và `Authorization: Bearer <token>`).
  - Kiểm tra thẩm quyền qua `verify_dataset_access(account, dataset_id, db)`: truy vấn thời gian thực danh sách dataset được cấp phép của tài khoản trong `dataset_grants`. Nếu không có quyền, quăng lỗi `403 Forbidden` ngay lập tức.
  - Kiểm tra ranh giới dữ liệu chặt chẽ: truy vấn `ExtractedImage` phải đồng thời khớp `ExtractedImage.id == image_id`, `ExtractedImage.dataset_id == dataset_id`, và join với `SourceVersion` để xác nhận `SourceVersion.source_id == source_id`. Ngăn chặn hoàn toàn việc đoán UUID ảnh để truy cập trái phép chéo dataset (IDOR / Cross-Tenant mitigation - T-07-02).
  - Kiểm tra sự tồn tại của tệp trên đĩa lưu trữ (`os.path.exists`), trả lỗi 404 có thông điệp rõ ràng nếu tệp thất lạc.
  - Trả về `FileResponse` với MIME type tương ứng, đính kèm các header bảo mật: `Cache-Control: private, max-age=3600` và `X-Content-Type-Options: nosniff`.
- Cập nhật [backend/app/main.py](file:///D:/KhacNghia/RAG/backend/app/main.py):
  - Đăng ký `images.router` vào ứng dụng FastAPI.
  - Tinh chỉnh middleware `security_headers` chỉ gán giá trị mặc định `Cache-Control: no-store` khi response chưa thiết lập header này, bảo toàn chỉ thị cache riêng cho FileResponse hình ảnh.
- Cập nhật [backend/app/auth/policy.py](file:///D:/KhacNghia/RAG/backend/app/auth/policy.py) bổ sung `verify_dataset_access`.
- **Commit:** `feat(phase-07-02): implement secure ACL-fenced image delivery endpoint` (`ec8bf9b`).

### 2. Integration Tests for Image API ACL & Live Scope Recheck (Task 07-02-02)
- Xây dựng bộ kiểm thử tích hợp [backend/tests/integration/test_image_api_security.py](file:///D:/KhacNghia/RAG/backend/tests/integration/test_image_api_security.py) bao phủ 7 kịch bản an ninh:
  1. `test_get_image_success_for_authorized_technician`: Kỹ thuật viên có quyền tải ảnh thành công (200 OK), nhận đúng nội dung nhị phân và các header bảo mật (`Cache-Control: private, max-age=3600`, `X-Content-Type-Options: nosniff`).
  2. `test_get_image_forbidden_for_unauthorized_dataset`: Kỹ thuật viên yêu cầu ảnh thuộc dataset chưa được cấp quyền bị từ chối 403 Forbidden.
  3. `test_live_scope_recheck_revocation`: Kỹ thuật viên ban đầu tải được ảnh (200 OK), sau khi bị admin xóa quyền trong bảng `dataset_grants`, yêu cầu tải lại ngay lập tức bị từ chối 403 Forbidden (Live Scope Recheck - T-07-03, AUTH-04).
  4. `test_unauthenticated_request_rejected`: Yêu cầu không có thông tin đăng nhập bị từ chối 401 Unauthorized.
  5. `test_get_image_cross_tenant_idor_rejected`: Kỹ thuật viên dùng dataset được cấp quyền nhưng truyền `image_id` thuộc dataset khác bị từ chối 404 Not Found (chống IDOR).
  6. `test_get_image_physical_file_missing_returns_404`: Tệp vật lý trên đĩa bị thiếu trả về 404.
  7. `test_admin_can_access_any_dataset_image`: Admin có quyền truy cập toàn bộ hình ảnh trên mọi dataset.
- **Commit:** `feat(phase-07-02): add integration tests for image API ACL and live scope recheck` (`c7e60d7`).

---

## Kết quả kiểm thử

Lệnh thực thi kiểm thử:
```bash
docker compose run --rm -v "${PWD}/backend:/app/backend" --no-deps backend-test pytest tests/integration/test_image_api_security.py -v
```
Kết quả:
```
tests/integration/test_image_api_security.py::test_get_image_success_for_authorized_technician PASSED [ 14%]
tests/integration/test_image_api_security.py::test_get_image_forbidden_for_unauthorized_dataset PASSED [ 28%]
tests/integration/test_image_api_security.py::test_live_scope_recheck_revocation PASSED [ 42%]
tests/integration/test_image_api_security.py::test_unauthenticated_request_rejected PASSED [ 57%]
tests/integration/test_image_api_security.py::test_get_image_cross_tenant_idor_rejected PASSED [ 71%]
tests/integration/test_image_api_security.py::test_get_image_physical_file_missing_returns_404 PASSED [ 85%]
tests/integration/test_image_api_security.py::test_admin_can_access_any_dataset_image PASSED [100%]

======================== 7 passed, 1 warning in 6.07s ==========================
```

Kiểm tra hồi quy và ranh giới kiến trúc:
```bash
docker compose run --rm -v "${PWD}/backend:/app/backend" --no-deps backend-test pytest tests/unit/test_module_boundaries.py tests/integration/test_report_scope_recheck.py -v
======================== 15 passed, 1 warning in 5.37s =========================
```

---

## Trạng thái và bước tiếp theo

Plan 07-02 đã hoàn thành toàn bộ yêu cầu, sẵn sàng chuyển tiếp sang **Plan 07-03: Multimodal LLM Grounding & Retrieval Enrichment**.

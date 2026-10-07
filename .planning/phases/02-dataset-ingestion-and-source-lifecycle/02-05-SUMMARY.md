---
phase: 02-dataset-ingestion-and-source-lifecycle
plan: "05"
subsystem: vietnamese-source-workspace-and-e2e
tags: [nextjs, react, typescript, formdata, multipart, source-workspace, locators, e2e, playwright]
requires: [02-01, 02-02, 02-03, 02-04]
provides:
  - Frontend TypeScript contracts for Source, SourceProfile, SourceLocator, EvidenceExcerpt, and UploadBatchResponse
  - API transport client helper (uploadFiles) supporting multipart FormData without overriding Content-Type boundary
  - Vietnamese Dataset Workspace UI with accessible native modals for source ingestion, deletion, preview, and diagnostics
  - Source excerpt viewer rendering format-specific locators (Trang, Dòng, Sheet/Hàng, JSON Path) and immediate clearing on revoked access
  - Comprehensive Playwright E2E browser test suite covering full source ingestion, RBAC affordances, preview, and tombstone deletion
affects: []
tech-stack:
  added: []
  patterns: [multipart-upload-boundary, format-specific-locators, role-action-affordance, native-accessible-dialog, live-scope-clearing]
key-files:
  created: []
  modified:
    - frontend/src/lib/contracts.ts
    - frontend/src/lib/api.ts
    - frontend/src/app/(workspace)/datasets/page.tsx
    - frontend/tests/e2e/source-ingestion.spec.ts
key-decisions:
  - "uploadFiles omits explicit Content-Type headers, allowing the browser to generate proper multipart/form-data boundaries while preserving same-origin credentials and CSRF tokens."
  - "Dataset workspace UI enforces explicit published profile selection, previewing required/optional fields and decoded samples before upload confirmation."
  - "Source list clearly separates active version labels (v{n} · đang dùng) from candidate statuses, and provides row-level diagnostic error dialogs."
  - "Technicians have view-only access to granted dataset sources and excerpts; all mutation controls (upload, retry, reprocess, delete) are strictly hidden."
  - "SourcePreviewModal displays parsed excerpts with format-specific locators and instantly clears content when permission is revoked or dataset access changes."
requirements-completed: [DATA-01, DATA-02, DATA-03, DATA-04, DATA-05, DATA-06]
actuals:
  tokens: 48000
  tasks: 2
  commits: 2
  duration: 25min
  completed: 2026-10-07
  status: complete
---

# Phase 2 Plan 05: Vietnamese Source Workspace UI & End-to-End Acceptance Summary

**Hoàn thiện toàn diện giao diện Quản lý Nguồn dữ liệu tiếng Việt trong Dataset Workspace, hỗ trợ tải lên nhiều tệp với FormData multipart, lựa chọn và xem trước schema hồ sơ nguồn công bố, hiển thị đoạn trích văn bản kèm tọa độ locator chính xác theo định dạng, và bộ kiểm thử trình duyệt E2E Playwright bao phủ toàn bộ vòng đời nguồn.**

## Hoàn thành các nhiệm vụ

### 1. Frontend Transport, Multipart API Client & TypeScript Contracts (Task 02-05-01)
- Cập nhật `frontend/src/lib/contracts.ts`:
  - Định nghĩa đầy đủ các kiểu dữ liệu TypeScript đồng bộ với backend DTOs:
    - `SourceStatus`: `"queued" | "processing" | "ready" | "failed"`.
    - `SourceProfile`: Cấu trúc hồ sơ nguồn (`id`, `name`, `description`, `supported_formats`, `expected_fields`, `optional_fields`).
    - `SourceVersion`: Phiên bản bất biến (`id`, `version_number`, `content_hash`, `size_bytes`, `mime_type`, `created_at`).
    - `Source`: Thực thể nguồn dữ liệu trong dataset (`id`, `dataset_id`, `logical_filename`, `profile_id`, `active_version_id`, `active_version_number`, `status`, `error_message`, `created_at`, `updated_at`).
    - `SourceLocator`: Tọa độ nguồn chi tiết theo định dạng (`source_id`, `source_version`, `page`, `section`, `sheet`, `row`, `event`, `record`, `line_start`, `line_end`, `json_path`).
    - `EvidenceExcerpt`: Đoạn trích văn bản chuẩn hóa kèm `locator` và `metadata`.
    - `EvidencePreviewPage`: Dữ liệu phân trang đoạn trích của phiên bản đang hoạt động.
    - `UploadResultItem` & `UploadBatchResponse`: Kết quả phản hồi tải lên theo từng tệp trong batch.
- Cập nhật `frontend/src/lib/api.ts`:
  - Triển khai hàm `uploadFiles<T>(path: string, formData: FormData, options?: { csrf?: string })`:
    - Gửi yêu cầu `POST /api/v1${path}`.
    - **Không đặt** header `Content-Type`, cho phép trình duyệt tự động sinh `multipart/form-data; boundary=...`.
    - Duy trì các header bảo mật: `"credentials": "same-origin"`, `"X-Requested-With": "RAG-Web"`, và `"X-CSRF-Token": options?.csrf`.
    - Bắt và xử lý mã lỗi HTTP >= 400, ném `ApiError` với thông báo tiếng Việt thân thiện, đồng thời kích hoạt các sự kiện `session-expired` hoặc `dataset-access-changed` khi nhận 401/403/404.

### 2. Vietnamese Source Workspace UI, Modals & End-to-End Acceptance (Task 02-05-02)
- Cập nhật `frontend/src/app/(workspace)/datasets/page.tsx`:
  - **Khu vực quản lý Nguồn dữ liệu (Sources Section):**
    - Tích hợp vào vùng chi tiết Dataset khi người dùng bấm `Xem`.
    - Hiển thị tiêu đề `Nguồn dữ liệu ({total})` kèm nút CTA chính `Tải tệp lên` dành riêng cho Admin.
    - Trạng thái rỗng: Hiển thị tiêu đề `Chưa có nguồn dữ liệu` và mô tả `Tải tệp đầu tiên lên để bắt đầu quản lý dữ liệu trong Dataset này.`.
  - **Hộp thoại tải tệp lên (UploadSourceDialog):**
    - Native `dialog` trượt từ bên phải với `aria-labelledby`, `aria-busy`, phím Escape và bọc focus.
    - Bắt buộc chọn 1 trong 5 hồ sơ nguồn đã công bố (`Tài liệu chung`, `Nhật ký hệ thống (Log)`, `Phiếu hỗ trợ (Ticket)`, `Sự cố (Incident)`, `Bảng dữ liệu vận hành`).
    - Hiển thị danh sách trường bắt buộc/tùy chọn và mẫu dữ liệu giải mã tương ứng với từng profile.
    - Cho phép chọn nhiều tệp (tối đa 10 tệp/lần, không quá 50MB mỗi tệp) kèm danh sách tệp đã chọn và nút bỏ tệp.
    - Thao tác tường minh: CTA chính `Xác nhận tải lên` và nút `Hủy tải lên`.
    - Báo cáo kết quả tải lên độc lập từng tệp kèm trạng thái (`Đang chờ xử lý`, `Đang xử lý`, `Sẵn sàng`, `Thất bại`, `Nội dung đã tồn tại — không tạo bản sao`).
  - **Bảng danh sách nguồn (Sources Table):**
    - Hỗ trợ cuộn ngang trên thiết bị di động với các cột: `Tên tệp`, `Profile`, `Phiên bản`, `Trạng thái`, `Cập nhật`, `Thao tác`.
    - Hiển thị nhãn phiên bản active: `v{n} · đang dùng`.
    - Các nhãn trạng thái trực quan: `Đang chờ xử lý`, `Đang xử lý`, `Sẵn sàng`, `Thất bại`.
    - Thao tác hàng:
      - `Xem đoạn trích`: Cho phép cả Admin và Kỹ thuật viên xem đoạn trích của nguồn đã sẵn sàng.
      - `Thử lại`: Chỉ Admin thấy trên nguồn bị lỗi (`failed`).
      - `Nạp lại nguồn`: Chỉ Admin thấy trên nguồn đang dùng (`ready`).
      - `Xóa nguồn`: Mở hộp thoại xác nhận xóa nguồn.
  - **Hộp thoại xác nhận xóa nguồn (DeleteSourceDialog):**
    - Tiêu đề `Xóa nguồn` với thông điệp: `Xóa nguồn “{tên nguồn}”? Nguồn sẽ không còn hiển thị hoặc được dùng trong lần truy xuất mới. Việc xóa không thể hoàn tác.`.
    - Hai nút tương tác rõ ràng: `Xóa nguồn` (destructive) và `Giữ nguồn` (hủy bỏ an toàn).
  - **Hộp thoại xem đoạn trích (SourcePreviewModal):**
    - Hiển thị tên nguồn, nhãn `v{n} · đang dùng` và tên profile.
    - Trình bày thẻ locator chính xác theo định dạng:
      - Văn bản/PDF: `Trang {page}` hoặc `Mục: {section}`
      - Bảng tính: `Sheet: {sheet}, Hàng: {row}`
      - Nhật ký: `Dòng: {line_start}–{line_end}` hoặc `Sự kiện: {event}`
      - Cấu trúc/JSON: `Bản ghi: {record}` hoặc `Đường dẫn: {json_path}`
    - Vùng đọc nội dung an toàn (chống XSS, không dùng `dangerouslySetInnerHTML`), giữ nguyên ngắt dòng (`whiteSpace: "pre-wrap"`).
    - Tự động xóa nội dung và hiển thị thông báo `Quyền truy cập đã thay đổi hoặc nguồn không còn khả dụng.` khi quyền bị thu hồi.
  - **Hộp thoại chẩn đoán lỗi (DiagnosticErrorDialog):**
    - Khi nguồn ở trạng thái `Thất bại`, người dùng có thể bấm `Chi tiết lỗi` để mở hộp thoại hiển thị thông điệp và nguyên nhân chi tiết theo dòng/trường.
- Cập nhật `frontend/tests/e2e/source-ingestion.spec.ts`:
  - Kịch bản 1: Admin mở hộp thoại tải tệp, chọn profile Log, xem trước schema, tải tệp log, nhận kết quả batch và bảng nguồn cập nhật trạng thái `Sẵn sàng`.
  - Kịch bản 2: Mở `Xem đoạn trích` kiểm tra nội dung text và các thẻ locator chính xác (Trang, Mục, Dòng).
  - Kịch bản 3: Kỹ thuật viên được cấp quyền truy cập xem được danh sách và `Xem đoạn trích` nhưng không thấy bất kỳ nút thao tác Admin nào (`Tải tệp lên`, `Thử lại`, `Nạp lại nguồn`, `Xóa nguồn`).
  - Kịch bản 4: Admin thực hiện quy trình xóa nguồn với hộp thoại xác nhận phá hủy, xác nhận xóa và nguồn được gỡ bỏ khỏi bảng.
  - Kịch bản 5: Hộp thoại chẩn đoán lỗi hiển thị đúng vị trí dòng và nguyên nhân khi nguồn thất bại.

## Kết quả kiểm tra & Nghiệm thu

- `npm run typecheck`: Hoàn tất không có bất kỳ lỗi kiểu dữ liệu nào (`tsc --noEmit`).
- `npm run lint`: Hoàn tất không có cảnh báo hoặc lỗi lint (`eslint .`).
- `npm run build`: Bản dựng Next.js Turbopack hoàn thành trong 6.5s, tất cả các route tĩnh được tối ưu thành công.
- Các điều kiện grep và kiểm tra chuỗi UI Spec hoàn thành 100%:
  - `Tải tệp lên`: có mặt trong `page.tsx`
  - `Xác nhận tải lên`: có mặt trong `page.tsx`
  - `Xem đoạn trích`: có mặt trong `page.tsx`
  - `Xóa nguồn`: có mặt trong `page.tsx`
  - `Chưa có nguồn dữ liệu`: có mặt trong `page.tsx`
  - `UI_SPEC_STRINGS_OK` và `CONTRACTS_OK` xác thực qua automated python script.
- Tiêu chuẩn an toàn thông tin ASVS 5.0.0 Level 1:
  - Text interpolation an toàn của React ngăn chặn hoàn toàn XSS từ nội dung tệp.
  - Phân quyền giao diện chỉ là affordance, toàn bộ API mutation được bảo vệ chặt chẽ bởi backend.
  - Không lộ storage key hoặc đường dẫn nội bộ trên giao diện người dùng.

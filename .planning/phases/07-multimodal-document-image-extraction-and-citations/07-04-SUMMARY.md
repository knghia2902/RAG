---
phase: 07-multimodal-document-image-extraction-and-citations
plan: "04"
subsystem: frontend-image-citations-and-lightbox
tags: [frontend, nextjs, react, ui, citation, lightbox, evidence-preview, pan-zoom]
requires: ["07-02", "07-03"]
provides:
  - Frontend contracts with image fields in frontend/src/lib/contracts.ts
  - EvidencePreview image display with zoom-in trigger and graceful error handling in frontend/src/components/EvidencePreview.tsx
  - ImageLightboxModal component with pan, zoom, scale controls and keyboard support in frontend/src/components/ImageLightboxModal.tsx
  - Inline chat markdown image rendering with URL sanitization (T-07-06) and cited images gallery in frontend/src/app/(workspace)/chat/page.tsx
  - Full frontend Turbopack production build verification with 11 static routes
affects: []
tech-stack:
  added: [ImageLightboxModal, Pan & Zoom, Markdown Image Parsing, Dual UI Citations]
  patterns: [dual-citation-display, pan-zoom-lightbox, xss-url-sanitization, graceful-image-error-fallback]
key-files:
  created:
    - frontend/src/components/ImageLightboxModal.tsx
  modified:
    - frontend/src/lib/contracts.ts
    - frontend/src/components/EvidencePreview.tsx
    - frontend/src/app/(workspace)/chat/page.tsx
key-decisions:
  - "Bổ sung image_id, image_url và caption vào SourceLocator, CitationItem và CitationPreviewDetail để luân chuyển dữ liệu hình ảnh xuyên suốt ứng dụng (D-05)."
  - "Xây dựng khối hiển thị hình ảnh trích dẫn trong EvidencePreview nằm giữa Tọa độ nguồn và Đoạn trích nguyên bản, hỗ trợ phóng to và bắt lỗi phân quyền/ảnh hỏng (D-05, D-08)."
  - "Tạo ImageLightboxModal hỗ trợ phóng to (scale 0.5 - 3.0), thu nhỏ, đặt lại tỉ lệ 1:1, kéo di chuyển (pan), cuộn chuột zoom và phím tắt Escape (D-06)."
  - "Triển khai hàm renderMessageContent phân tích cú pháp Markdown image ![alt](url) kèm kiểm tra an toàn URL (isSafeImageUrl) triệt tiêu nguy cơ XSS theo T-07-06."
  - "Hiển thị thư viện ảnh trích dẫn (thumbnail cards) dưới câu trả lời của trợ lý cho các ảnh chưa được chèn trực tiếp vào nội dung văn bản."
requirements-completed: [DATA-03, RETR-03]
actuals:
  tasks: 3
  commits: 3
  duration: 15min
  completed: 2026-10-15
  status: complete
---

# Phase 07 Plan 04: Frontend Image Citations, Evidence Preview & Lightbox Modal Summary

**Triển khai thành công toàn bộ giao diện trực quan hóa hình ảnh tài liệu đa phương thức trên Frontend Next.js / React: hiển thị hình ảnh trích dẫn trong panel `EvidencePreview`, hỗ trợ xem ảnh kích thước lớn qua modal `ImageLightboxModal` với khả năng phóng to/thu nhỏ (pan & zoom), và render hình ảnh Markdown an toàn (XSS-sanitized) ngay trong khung trò chuyện Chat.**

---

## Các nhiệm vụ đã hoàn thành

### 1. Update Frontend Contracts & EvidencePreview Image Display (Task 07-04-01)
- Cập nhật [frontend/src/lib/contracts.ts](file:///D:/KhacNghia/RAG/frontend/src/lib/contracts.ts):
  - Bổ sung `image_id?: string;`, `image_url?: string;` vào `SourceLocator` và alias `CitationLocator`.
  - Bổ sung `image_id?: string;`, `image_url?: string;`, `caption?: string;` vào `CitationItem` và `CitationPreviewDetail`.
- Cập nhật [frontend/src/components/EvidencePreview.tsx](file:///D:/KhacNghia/RAG/frontend/src/components/EvidencePreview.tsx):
  - Nhận thêm prop tùy chọn `onImageClick?: (url: string, alt?: string, caption?: string) => void`.
  - Khởi tạo state `imageError` và reset tự động khi citation thay đổi.
  - Chèn khối hiển thị ảnh trích dẫn nằm giữa khối **Tọa độ nguồn** và khối **Đoạn trích nguyên bản** (D-05, 07-UI-SPEC):
    - Tiêu đề nhỏ: `"Hình ảnh trích dẫn tại trang " + citation.locator.page:`.
    - Khung chứa bo tròn với nền nhạt `#f1f5f9`, border `1px solid #d7e1e8`.
    - Thẻ `<img>` với `maxHeight: 260px`, `objectFit: contain`, `cursor: zoom-in`.
    - Nút phụ trợ phía dưới: `"🔍 Phóng to chi tiết (Xem kích thước gốc)"`.
    - Xử lý lỗi load ảnh hoặc bị thu hồi quyền: hiển thị thông báo alert thân thiện thay vì ảnh vỡ.
- **Commit:** `feat(phase-07-04): add image fields to contracts and render cited image in EvidencePreview` (`4fd260c`).

### 2. Create ImageLightboxModal Component (Task 07-04-02)
- Tạo component [frontend/src/components/ImageLightboxModal.tsx](file:///D:/KhacNghia/RAG/frontend/src/components/ImageLightboxModal.tsx):
  - Lớp nền overlay tối mờ `background: rgba(15, 23, 42, 0.88)` che toàn màn hình (`z-index: 9999`).
  - Khóa cuộn trang `document.body.style.overflow = "hidden"` khi modal đang mở và khôi phục khi đóng.
  - Phím tắt `Escape` hoặc click trực tiếp vào backdrop bên ngoài để đóng modal.
  - Quản lý mức thu phóng (`scale`: từ 0.5 đến 3.0, bước 0.25) và tọa độ kéo di chuyển (`position: { x, y }`).
  - Hỗ trợ cuộn chuột (mouse wheel) để phóng to / thu nhỏ linh hoạt.
  - Hỗ trợ nhấn giữ chuột trái và kéo (drag & pan) để di chuyển vùng quan sát sơ đồ lớn.
  - Thanh công cụ trên cùng: Nút Phóng to (+), Thu nhỏ (-), Đặt lại 1:1 gốc, và nút Đóng (✕).
  - Thanh thông tin phía dưới hiển thị chú thích, tên file và mẹo thao tác cho kỹ thuật viên.
- **Commit:** `feat(phase-07-04): create ImageLightboxModal component with pan and zoom` (`6dc1be4`).

### 3. Chat Page Inline Image Rendering & Lightbox Binding (Task 07-04-03)
- Cập nhật [frontend/src/app/(workspace)/chat/page.tsx](file:///D:/KhacNghia/RAG/frontend/src/app/(workspace)/chat/page.tsx):
  - Khai báo state `lightboxImage: { url: string; alt?: string; caption?: string } | null = null`.
  - Triển khai hàm `isSafeImageUrl(url)` kiểm tra chặt chẽ URL ảnh, ngăn chặn triệt để các mã độc hại `javascript:`, `data:` (chống XSS theo T-07-06).
  - Triển khai hàm `renderMessageContent(content, onImageClick)` nhận diện cú pháp Markdown image `![alt](url)` và render thẻ ảnh bo góc kèm chú thích, nhấp chuột để mở Lightbox Modal.
  - Bổ sung khối gallery hình ảnh trích dẫn (thumbnail cards) đối với các trích dẫn có ảnh đính kèm nhưng chưa được nhúng trực tiếp trong văn bản.
  - Kết nối prop `onImageClick` của `<EvidencePreview>` vào state `setLightboxImage` của trang Chat.
  - Render `<ImageLightboxModal>` toàn màn hình khi `lightboxImage` khác null.
- **Commit:** `feat(phase-07-04): bind inline image thumbnails in chat and lightbox modal` (`167b0b3`).

---

## Kết quả kiểm tra và xác minh

### 1. Kiểm tra build Frontend (Next.js Turbopack)
```bash
docker compose exec frontend npm run build
```
Kết quả:
```
▲ Next.js 16.3.8 (Turbopack)
✓ Running next.config.ts took 55ms
  Creating an optimized production build ...
✓ Compiled successfully in 673ms
  Running TypeScript ...
  Finished TypeScript in 2.7s ...
  Collecting page data using 11 workers ...
✓ Generating static pages using 11 workers (11/11) in 363ms
  Finalizing page optimization ...

Route (app)
┌ ○ /
├ ○ /_not-found
├ ○ /accounts
├ ○ /change-password
├ ○ /chat
├ ○ /configuration
├ ○ /datasets
├ ○ /incidents
├ ○ /login
└ ○ /reports

○  (Static)  prerendered as static content
```

### 2. Kiểm tra hồi quy toàn diện Backend & API
```bash
docker compose run --rm -v "${PWD}/backend:/app/backend" --no-deps backend-test pytest tests/unit/ tests/integration/test_image_api_security.py -v
```
Kết quả: **123 passed, 5 warnings in 19.82s**.

---

## Trạng thái Phase 7

Toàn bộ 4 kế hoạch của Phase 7 đã hoàn thành xuất sắc:
- **Plan 07-01**: Parser Extractor, ExtractedImage Model & Celery Pipeline.
- **Plan 07-02**: ACL-Fenced Image Serving API & Live Scope Recheck.
- **Plan 07-03**: Multimodal RAG Retrieval & Gemini Vision Generation.
- **Plan 07-04**: Frontend Citation Previews, Lightbox Pan/Zoom & Dual UI Display.

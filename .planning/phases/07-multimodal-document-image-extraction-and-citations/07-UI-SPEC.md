---
phase: 07
slug: multimodal-document-image-extraction-and-citations
status: approved
created: 2026-10-15
---

# Phase 07: Multimodal Document Image Extraction and Citations — UI Design Contract

## Scope & Intent
Phase 7 bổ sung tính năng trực quan hóa hình ảnh tài liệu kỹ thuật vào giao diện Web:
1. Hiển thị hình ảnh thumbnail trong câu trả lời Chat của trợ lý ảo khi câu hỏi liên quan đến sơ đồ kỹ thuật, hình ảnh minh họa hoặc màn hình cấu hình.
2. Hiển thị hình ảnh trích dẫn trong bảng xem trước bằng chứng nguồn (`EvidencePreview.tsx`) khi kỹ thuật viên click vào các thẻ trích dẫn `[1]`, `[2]`.
3. Cung cấp Lightbox Modal (`ImageLightboxModal.tsx`) cho phép phóng to, thu nhỏ và quan sát chi tiết độ nét cao của các sơ đồ mạng, bảng datasheet.

## UI Components & Design Specifications

### 1. Khung Chat (`frontend/src/app/(workspace)/chat/page.tsx`)
- **Vị trí ảnh:** Hiển thị trực tiếp bên trong nội dung tin nhắn của trợ lý (hỗ trợ thẻ Markdown Image `![mô tả](/api/v1/datasets/.../images/...)` hoặc khối card ảnh đính kèm phía dưới tin nhắn).
- **Kích thước Thumbnail:** Chiều cao tối đa 240px, bo góc `rounded-lg`, đường viền `1px solid #d7e1e8`, nền nhẹ `#f8fafc`.
- **Tương tác:** Con trỏ chuột chuyển thành kính lúp `cursor-zoom-in`, hover có hiệu ứng bóng đổ nhẹ `hover:shadow-md`. Nhấp chuột vào ảnh sẽ mở Lightbox Modal.

### 2. Panel Xem Bằng Chứng Nguồn (`frontend/src/components/EvidencePreview.tsx`)
- **Vị trí hiển thị:** Nằm giữa khối **Tọa độ nguồn** (Trang, Dòng, Mục) và khối **Đoạn trích nguyên bản**.
- **Tiêu đề khối:** "Hình ảnh trích dẫn (Trang X):" với nhãn kích thước nhỏ, màu `#527080`, font chữ in đậm.
- **Khung chứa ảnh:**
  - Nền xám nhạt chống chói `#f1f5f9`, border bo tròn `rounded-md`.
  - Ảnh tự động căn giữa, tỷ lệ khung hình `object-contain`, chiều cao tối đa 260px.
  - Phía dưới ảnh có nút nhỏ: "🔍 Phóng to chi tiết (Xem kích thước gốc)".
- **Xử lý mất quyền (Live Scope Recheck):** Nếu phiên đăng nhập bị thu hồi quyền dataset, khung ảnh hiển thị trạng thái bị từ chối truy cập (HTTP 403) đồng bộ với thông báo cảnh báo hiện tại của EvidencePreview.

### 3. Modal Phóng To Chi Tiết (`ImageLightboxModal.tsx`)
- **Lớp nền (Backdrop):** Màu đen mờ `rgba(15, 23, 42, 0.85)` che toàn màn hình, hỗ trợ đóng khi click ra ngoài hoặc nhấn phím `Escape`.
- **Thanh công cụ (Toolbar):**
  - Góc trên bên phải: Nút Đóng `✕`, Nút Phóng to `+`, Nút Thu nhỏ `-`, Nút Đặt lại kích thước `1:1`.
  - Góc dưới bên trái: Hiển thị tên file tài liệu gốc, số trang và mô tả ảnh.
- **Tương tác phóng to:** Cho phép cuộn chuột (scroll wheel) để zoom in/zoom out và kéo chuột để di chuyển (pan) vùng xem sơ đồ.

## Acceptance Criteria for UI Verification
- Kỹ thuật viên nhấp vào thẻ trích dẫn [1] trong đoạn chat có trích dẫn từ datasheet/hướng dẫn ESXi, panel EvidencePreview mở ra và hiển thị rõ ràng hình ảnh của trang tài liệu tương ứng.
- Nhấp vào ảnh mở modal phóng to, hình ảnh giữ nguyên độ phân giải sắc nét của sơ đồ và các dòng chữ kỹ thuật.
- Khi người dùng đăng xuất hoặc tài khoản bị gỡ quyền dataset, hình ảnh không thể tải được và hiển thị thông báo an toàn.

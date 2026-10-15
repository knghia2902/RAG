---
phase: 08-ui-redesign-with-pastel-green-and-white-theme
plan: "02"
subsystem: frontend-chat-and-multimodal-citations
tags: [chat, citations, drawer, evidence-preview, lightbox, pan-zoom, floating-dock, pastel-green]
requires: ["08-01"]
provides:
  - Redesigned Knowledge Chat page in frontend/src/app/(workspace)/chat/page.tsx with pastel mint user bubbles, white AI bubbles, AI avatar, and inline interactive pill citations
  - Responsive Slide-over Drawer in frontend/src/components/EvidencePreview.tsx with backdrop blur, metadata badges, locator pills, image preview, and source excerpt
  - Floating Dock Image Lightbox Modal in frontend/src/components/ImageLightboxModal.tsx with glassmorphism controls, zoom in/out, 1:1 reset, and deep dark backdrop
affects: [08-03, 08-04]
tech-stack:
  added: []
  patterns: [slide-over-drawer, floating-dock-controls, inline-pill-badges, responsive-chat-bubbles]
key-files:
  created: []
  modified:
    - frontend/src/app/(workspace)/chat/page.tsx
    - frontend/src/components/EvidencePreview.tsx
    - frontend/src/components/ImageLightboxModal.tsx
key-decisions:
  - "Tái thiết kế giao diện Hỏi đáp Tri thức (/chat) với bong bóng tin nhắn User xanh mint pastel (#ecfdf5, #a7f3d0), tin nhắn AI nền trắng kèm avatar robot xanh pastel và số trích dẫn [1], [2] dạng pill badge tương tác (D-09, D-10)."
  - "Chuyển đổi EvidencePreview thành Slide-over Drawer trượt từ mép phải (~480px) kèm backdrop mờ, giải phóng toàn bộ không gian ngang cho hội thoại mà vẫn cho phép kiểm tra tọa độ nguồn và ảnh trích dẫn trực quan (D-11)."
  - "Nâng cấp ImageLightboxModal với thanh dock công cụ nổi ở mép đáy màn hình mang phong cách kính mờ glassmorphism (Zoom +/-, 1:1, Đóng) và hiển thị tỷ lệ % trên phông nền tối mờ sâu (D-12)."
requirements-completed: [RETR-03]
actuals:
  tasks: 3
  commits: 3
  duration: 15min
  completed: 2026-10-15
  status: complete
---

# Phase 08 Plan 02: Knowledge Chat, Multimodal Citations & Lightbox Redesign Summary

**Tái thiết kế hoàn thiện trải nghiệm Hỏi đáp Tri thức (`/chat`), trích dẫn đa phương thức và đối chiếu bằng chứng nguồn: bong bóng hội thoại pastel mềm mại, thẻ trích dẫn pill badge tương tác, Slide-over Drawer `EvidencePreview` từ cạnh phải và trình phóng to ảnh `ImageLightboxModal` với thanh dock công cụ nổi kính mờ (Floating Dock Glassmorphism).**

---

## Các nhiệm vụ đã hoàn thành

### 1. Tái cấu trúc Giao diện Chat & Trích dẫn Inline (Task 08-02-01)
- Cập nhật [frontend/src/app/(workspace)/chat/page.tsx](file:///D:/KhacNghia/RAG/frontend/src/app/%28workspace%29/chat/page.tsx):
  - **Bong bóng tin nhắn người dùng (User):** Canh lề phải (`max-width: 80%`), nền xanh mint pastel `var(--color-pastel-mint)` (`#ecfdf5`), viền mỏng `var(--color-mint-border)` (`#a7f3d0`), bo góc mềm mại `16px 16px 4px 16px`.
  - **Bong bóng tin nhắn Trợ lý AI:** Canh lề trái (`max-width: 85%`), nền trắng tinh khôi (`#ffffff`), viền mỏng `var(--border-subtle)` (`#e2e8f0`), bo góc `16px 16px 16px 4px`, đổ bóng nhẹ `var(--shadow-soft)`. Kèm Avatar tròn xanh mint 36px với biểu tượng robot tri thức.
  - **Trích dẫn số `[1]`, `[2]` inline:** Tự động nhận diện trong nội dung văn bản và biến đổi thành các nút pill badge pastel mint (`#d1fae5`, chữ `#065f46`), hỗ trợ click trực tiếp mở ngăn kéo xem bằng chứng với hiệu ứng hover nhấc nhẹ (`transform: translateY(-1px)`).
  - **Danh sách nguồn đối chiếu ở chân tin nhắn:** Thẻ mini bo góc 8px viền mỏng hiển thị số trích dẫn, tọa độ (Trang/Dòng/Mục) và icon camera 📷 nếu có hình ảnh đính kèm.
  - **Khung nhập liệu đáy:** Textarea bo góc 10px với focus ring xanh mint `3px rgba(16, 185, 129, 0.15)`, nút CTA "Gửi câu hỏi" màu xanh pastel đậm `#10b981`.
  - **Trạng thái trống (Empty State):** Chuẩn hóa copywriting "Bắt đầu cuộc hội thoại mới" kèm icon trò chuyện trong vòng tròn mint pastel.
- *Commit:* `28dd1d2 feat(phase-08-02): redesign chat page and inline citations`

### 2. Thiết kế EvidencePreview dạng Slide-over Drawer (Task 08-02-02)
- Cập nhật [frontend/src/components/EvidencePreview.tsx](file:///D:/KhacNghia/RAG/frontend/src/components/EvidencePreview.tsx):
  - **Kiến trúc Slide-over Drawer:** Chuyển đổi từ cột cố định 360px sang Drawer trượt từ cạnh phải (`width: 480px; max-width: 92vw; position: fixed; z-index: 50`) kèm lớp phủ nền mờ `backdrop-filter: blur(2px)`. Tự động giải phóng toàn bộ diện tích chiều ngang cho khung hội thoại chính.
  - **Thanh Header Drawer:** Tiêu đề "Chi tiết Bằng chứng Nguồn", badge định dạng tệp (`PDF`, `DOCX`, `LOG`, `SHEET`), nút đóng `✕` với thuộc tính tiếp cận `aria-label="Đóng bảng xem trước bằng chứng"` và phím tắt ESC.
  - **Thẻ vị trí nguồn (Locator):** Tọa độ Trang, Mục, Dòng, Sheet hiển thị dạng thẻ pill badge màu xanh lục bảo rõ ràng.
  - **Khung ảnh trích dẫn:** Thumbnail chất lượng cao bo góc 12px viền mint pastel kèm nút "🔍 Phóng to xem chi tiết sơ đồ".
  - **Đoạn trích nguyên bản:** Khung văn bản font monospace trên nền pastel nhạt với vạch highlight xanh lục bảo `4px solid var(--color-primary-green)` ở mép trái.
  - **Xử lý thu hồi quyền (Live Scope Recheck):** Hiển thị cảnh báo màu đỏ hồng pastel chuẩn mực khi quyền truy cập bị thu hồi hoặc hết hạn.
- *Commit:* `814abd1 feat(phase-08-02): redesign evidence preview as slide-over drawer`

### 3. Tái thiết kế ImageLightboxModal với Floating Dock kính mờ (Task 08-02-03)
- Cập nhật [frontend/src/components/ImageLightboxModal.tsx](file:///D:/KhacNghia/RAG/frontend/src/components/ImageLightboxModal.tsx):
  - **Phông nền tối mờ sâu:** Nền `rgba(15, 23, 42, 0.85)` kết hợp `backdrop-filter: blur(6px)` tạo độ tương phản cao, làm nổi bật sơ đồ kỹ thuật.
  - **Thanh công cụ nổi (Floating Dock):** Đặt nổi ở đáy màn hình (`bottom: 28px; left: 50%; transform: translateX(-50%)`) với phong cách kính mờ glassmorphism (`backdrop-filter: blur(14px); background: rgba(30, 41, 59, 0.75); border: 1px solid rgba(255, 255, 255, 0.18)`), bo tròn hoàn toàn `border-radius: 9999px`.
  - **Hệ thống nút điều khiển trực quan:**
    - Nút Thu nhỏ (`-`) với `aria-label="Thu nhỏ ảnh sơ đồ kỹ thuật"`.
    - Badge hiển thị tỷ lệ thu phóng dạng % (ví dụ: `100%`, `150%`).
    - Nút Phóng to (`+`) với `aria-label="Phóng to ảnh sơ đồ kỹ thuật"`.
    - Nút Đặt lại kích thước gốc (`1:1`) với `aria-label="Đặt lại kích thước ban đầu"`.
    - Nút Đóng (`✕`) màu đỏ nổi bật với `aria-label="Đóng trình xem ảnh"`.
  - **Tương tác trực quan:** Hỗ trợ cuộn chuột zoom mượt mà, giữ chuột kéo pan tự do khi phóng to và phím Escape đóng modal.
- *Commit:* `720ee7e feat(phase-08-02): redesign image lightbox modal with floating dock`

---

## Kết quả kiểm thử & xác minh

1. **Kiểm tra kiểu dữ liệu (TypeScript Typecheck):**
   - Lệnh: `docker compose exec frontend npm run typecheck`
   - Kết quả: `tsc --noEmit --incremental false` hoàn thành thành công với **0 lỗi** (Exit Code 0).
2. **Kiểm tra biên dịch sản xuất (Production Build):**
   - Lệnh: `docker compose exec frontend npm run build`
   - Kết quả: Next.js 16.3.8 (Turbopack) biên dịch thành công toàn bộ **11 static routes** bao gồm `/chat` trong 808ms.
3. **Kiểm tra Lint:**
   - Cả 3 tệp `chat/page.tsx`, `EvidencePreview.tsx`, và `ImageLightboxModal.tsx` không có bất kỳ lỗi lint nào.
4. **Tính nguyên tử của Commits:**
   - Task 1: `28dd1d2 feat(phase-08-02): redesign chat page and inline citations`
   - Task 2: `814abd1 feat(phase-08-02): redesign evidence preview as slide-over drawer`
   - Task 3: `720ee7e feat(phase-08-02): redesign image lightbox modal with floating dock`

---

## Bước tiếp theo (Next Steps)
- Tiến hành thực thi **Plan 08-03**: Tái thiết kế giao diện Phân tích Sự cố (`/incidents`), sơ đồ tiến trình sự kiện WMS-TMS `Timeline.tsx` và Quản trị Dataset (`/datasets`, `DatasetGrantPanel.tsx`).

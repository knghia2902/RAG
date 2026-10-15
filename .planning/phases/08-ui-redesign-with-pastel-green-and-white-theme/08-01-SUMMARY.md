---
phase: 08-ui-redesign-with-pastel-green-and-white-theme
plan: "01"
subsystem: frontend-design-system-and-workspace-shell
tags: [design-system, css-tokens, pastel-green, sidebar, workspace-layout, mobile-drawer, login, auth]
requires: []
provides:
  - Design Tokens and CSS Variables in frontend/src/app/globals.css for surfaces, pastel green, micro-shadows, and typography
  - Standardized utility classes (.btn-primary, .btn-secondary, .btn-danger, .badge-pastel-green, .badge-pastel-amber, .badge-pastel-rose, .badge-pastel-slate, .card-soft)
  - Redesigned Sidebar component in frontend/src/components/Sidebar.tsx with white surface, pastel green branding, SVG icons, and footer profile card
  - Responsive App Shell in frontend/src/app/(workspace)/layout.tsx with sticky desktop sidebar and mobile off-canvas drawer with backdrop blur
  - Redesigned Login page in frontend/src/app/login/page.tsx with centered soft card, pearl gray canvas, and primary CTA
  - Redesigned Change Password page in frontend/src/app/change-password/page.tsx with matching card styling and security branding
affects: [08-02, 08-03, 08-04]
tech-stack:
  added: []
  patterns: [css-variables-tokens, high-taste-pastel-theme, mobile-drawer-pattern, accessible-cta-buttons]
key-files:
  created: []
  modified:
    - frontend/src/app/globals.css
    - frontend/src/components/Sidebar.tsx
    - frontend/src/app/(workspace)/layout.tsx
    - frontend/src/app/login/page.tsx
    - frontend/src/app/change-password/page.tsx
key-decisions:
  - "Định nghĩa toàn bộ Design Tokens tập trung qua CSS Variables trong globals.css (không thêm runtime dependency) đạt chuẩn WCAG AA và tốc độ nạp trang tức thì (D-05, D-06)."
  - "Tái cấu trúc Sidebar nền trắng tinh tế (#ffffff) với vạch active marker 3px xanh pastel (#10b981) và chân trang chứa avatar tròn viết tắt chữ cái cùng role pill badge (D-01, D-02, D-03)."
  - "Hỗ trợ trải nghiệm Responsive trượt êm ái trên thiết bị di động (max-width: 768px) với mobile header, hamburger toggle và lớp nền mờ backdrop blur (D-04)."
  - "Canh giữa form đăng nhập và đổi mật khẩu trong thẻ .card-soft bo góc 16px, đổ bóng mềm mại, nút submit xanh pastel đậm có aria-label tương thích 100% với Playwright E2E suite."
requirements-completed: [DATA-05, RETR-03]
actuals:
  tasks: 3
  commits: 3
  duration: 15min
  completed: 2026-10-15
  status: complete
---

# Phase 08 Plan 01: Design Tokens, Global CSS & Workspace Shell Redesign Summary

**Triển khai thành công nền tảng Design System chuẩn mực cho ứng dụng Web Logistics RAG: hệ thống CSS Variables trắng tinh khôi kết hợp xanh lá pastel (Sage & Mint), thanh điều hướng Sidebar hiện đại kèm mobile drawer, và bộ đôi màn hình xác thực Đăng nhập & Đổi mật khẩu.**

---

## Các nhiệm vụ đã hoàn thành

### 1. Định nghĩa Design Tokens & Global Styles (Task 08-01-01)
- Cập nhật toàn bộ [globals.css](file:///D:/KhacNghia/RAG/frontend/src/app/globals.css) với hệ thống Design Tokens:
  - **Surfaces**: `--bg-app: #f8fafc`, `--bg-card: #ffffff`, `--bg-subtle: #f1f5f9`.
  - **Pastel Green Accent**: `--color-pastel-50: #f0fdf4`, `--color-pastel-100: #dcfce7`, `--color-pastel-mint: #ecfdf5`, `--color-mint-border: #a7f3d0`, `--color-primary-green: #10b981`, `--color-primary-hover: #059669`, `--color-emerald-dark: #047857`, `--color-emerald-deep: #065f46`.
  - **Neutral & Borders**: `--color-text-main: #0f172a`, `--color-text-muted: #64748b`, `--border-subtle: #e2e8f0`, `--border-divider: #f1f5f9`.
  - **Micro-shadows**: `--shadow-soft`, `--shadow-card`, `--shadow-floating`.
  - **Typography & Radius**: Font stack chuẩn hiện đại `-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Inter, sans-serif`, bán kính bo góc 8px, 12px, 16px, 9999px.
  - **Utility Classes**: `.btn-primary`, `.btn-secondary`, `.btn-danger`, `.badge-pastel-green`, `.badge-pastel-amber`, `.badge-pastel-rose`, `.badge-pastel-slate`, `.card-soft`, `.eyebrow`, `.error`, `.muted`.
- *Commit:* `1b35727 feat(phase-08-01): define design tokens and global styles in globals.css`

### 2. Tái cấu trúc Sidebar & Bố cục Workspace Shell (Task 08-01-02)
- Cập nhật [Sidebar.tsx](file:///D:/KhacNghia/RAG/frontend/src/components/Sidebar.tsx):
  - Bề mặt nền trắng tinh gọn (`#ffffff`), viền mỏng (`#e2e8f0`).
  - Logo thương hiệu nổi bật: Icon hộp logistics + mạng lưới AI gradient pastel xanh kèm tên "Logistics RAG" và badge "v1.0".
  - Giữ nguyên các định danh liên kết chính xác cho vai trò Quản trị viên và Kỹ thuật viên.
  - Mỗi mục điều hướng bổ sung Icon SVG inline chuẩn Lucide.
  - Trạng thái Active: nền mint pastel (`#ecfdf5`), chữ xanh ngọc bích đậm (`#047857`) và thanh đánh dấu 3px ở mép trái.
  - Thẻ người dùng cố định ở đáy: avatar tròn viết tắt chữ cái nền mint, hiển thị tên tài khoản, pill badge vai trò (`Quản trị viên` / `Kỹ thuật viên`), trạng thái "Local · localhost", và nút "Đăng xuất" thanh lịch.
- Cập nhật [layout.tsx](file:///D:/KhacNghia/RAG/frontend/src/app/(workspace)/layout.tsx):
  - Bố cục flex 2 cột desktop (`Sidebar` sticky cố định 260px và `main` canvas mở rộng).
  - Thanh Header di động trên màn hình nhỏ hiển thị logo thu nhỏ và nút Hamburger.
  - Ngăn kéo Sidebar dạng Off-canvas Drawer kèm lớp phủ làm mờ nền `backdrop-filter: blur(4px)`.
- *Commit:* `72443a9 feat(phase-08-01): redesign sidebar and mobile drawer workspace layout`

### 3. Tái thiết kế Giao diện Đăng nhập & Đổi mật khẩu (Task 08-01-03)
- Cập nhật [login/page.tsx](file:///D:/KhacNghia/RAG/frontend/src/app/login/page.tsx):
  - Bố cục canh giữa màn hình trên nền canvas xám ngọc trai (`#f8fafc`).
  - Khung đăng nhập `.card-soft` bo góc 16px, viền mỏng `#e2e8f0`, đổ bóng mềm mại `var(--shadow-card)`.
  - Icon logistics gradient xanh pastel, tiêu đề "Đăng nhập hệ thống", nhãn "Tên đăng nhập" và "Mật khẩu" sắc nét.
  - Nút CTA đăng nhập xanh pastel đậm `#10b981` với chữ hiển thị "Đăng nhập hệ thống" và `aria-label="Đăng nhập"` đảm bảo khả năng tiếp cận và tương thích tuyệt đối với Playwright E2E tests.
  - Dòng ghi chú bảo mật local Docker ở chân form.
- Cập nhật [change-password/page.tsx](file:///D:/KhacNghia/RAG/frontend/src/app/change-password/page.tsx):
  - Đồng bộ phong cách `.card-soft`, icon ổ khóa bảo mật gradient xanh pastel, và nút "Đổi mật khẩu" xanh pastel chuẩn mực.
- *Commit:* `e9db09f feat(phase-08-01): redesign login and change password pages`

---

## Kết quả kiểm thử & xác minh

1. **Kiểm tra kiểu dữ liệu (TypeScript Typecheck):**
   - Lệnh: `docker compose exec frontend npm run typecheck`
   - Kết quả: `tsc --noEmit --incremental false` hoàn thành với **0 lỗi** (Exit Code 0).
2. **Kiểm tra biên dịch sản xuất (Production Build):**
   - Lệnh: `docker compose exec frontend npm run build`
   - Kết quả: Next.js 16.3.8 (Turbopack) biên dịch thành công toàn bộ **11 static routes** (`/`, `/_not-found`, `/accounts`, `/change-password`, `/chat`, `/configuration`, `/datasets`, `/incidents`, `/login`, `/reports`) trong 31.4s.
3. **Tính nguyên tử của Commits:**
   - Cả 3 tasks đều được commit riêng biệt và có thông điệp commit rõ ràng theo đúng quy chuẩn GSD.

---

## Bước tiếp theo (Next Steps)
- Tiến hành thực thi **Plan 08-02**: Tái thiết kế giao diện Hỏi đáp Tri thức (`/chat`), bong bóng hội thoại pastel, thẻ trích dẫn, ngăn kéo trượt `EvidencePreview` và trình phóng to ảnh `ImageLightboxModal`.

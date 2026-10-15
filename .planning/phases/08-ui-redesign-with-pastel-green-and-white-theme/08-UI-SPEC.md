---
phase: 8
slug: ui-redesign-with-pastel-green-and-white-theme
status: draft
shadcn_initialized: false
preset: not applicable
created: 2026-10-15
---

# Phase 08 — UI Design Contract

> Visual and interaction contract for Phase 08: UI Redesign with Pastel Green and White Theme.
> Generated based on user decisions in `08-CONTEXT.md` and verified against 6 GSD UI quality dimensions.

---

## Design System

| Property | Value |
|----------|-------|
| Tool | none |
| Preset | not applicable |
| Component library | none |
| Icon library | inline SVG icons (Lucide-inspired, 0 runtime dependency) |
| Font | Modern Clean System Font Stack (`-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Inter, sans-serif`) |

---

## Spacing Scale

Declared values (strictly multiples of 4):

| Token | Value | Usage |
|-------|-------|-------|
| xs | 4px | Icon gaps, inline padding, badge vertical padding |
| sm | 8px | Compact element spacing, input vertical padding, button gaps |
| md | 16px | Default element spacing, card padding, table cell padding |
| lg | 24px | Section padding, modal header/body padding, drawer padding |
| xl | 32px | Layout gaps, grid gap between dashboard columns |
| 2xl | 48px | Major section breaks, login form top/bottom margin |
| 3xl | 64px | Page-level spacing on desktop workspace canvas |

Exceptions: none

---

## Typography

Constrained to exactly 4 hierarchical font sizes and 2 font weights:

| Role | Size | Weight | Line Height | Usage |
|------|------|--------|-------------|-------|
| Display | 28px | 600 | 1.25 | Tiêu đề trang chính, số liệu KPI tổng hợp trong báo cáo |
| Heading | 20px | 600 | 1.35 | Tiêu đề card, tiêu đề section, modal headers |
| Body | 15px | 400 | 1.60 | Nội dung tin nhắn chat, bảng dữ liệu, đoạn văn giải trình |
| Label | 13px | 600 | 1.40 | Pill badges trạng thái, tiêu đề cột bảng, trích dẫn, captions |

---

## Color

60/30/10 Split and Semantic Rules:

| Role | Value | Usage |
|------|-------|-------|
| Dominant (60%) | `#ffffff` / `#f8fafc` | Nền canvas toàn trang (`#f8fafc`), bề mặt chính card và chat body (`#ffffff`) |
| Secondary (30%) | `#ffffff` / `#f1f5f9` / `#e2e8f0` / `#64748b` | Bề mặt Sidebar/Header, viền phân cách mỏng (`#f1f5f9`), viền card (`#e2e8f0`), text phụ (`#64748b`) |
| Accent (10%) | `#10b981` / `#ecfdf5` / `#047857` | Sage & Mint Pastel dành riêng cho danh sách thành phần giới hạn bên dưới |
| Destructive | `#dc2626` / `#fef2f2` / `#b91c1c` | Nút xóa vĩnh viễn nguồn dữ liệu, thông báo lỗi critical, badge P1 |

### Accent Reserved For (Strict Whitelist — NEVER "all interactive elements")
1. Primary CTA action buttons (`button.btn-primary` with background `#10b981`, hover `#059669`, text `#ffffff`)
2. Active navigation item indicator and highlight background in Sidebar (`#ecfdf5` background, `#047857` text, 3px active border marker)
3. Citation pill badges `[1]`, `[2]` in AI chat responses (`#d1fae5` background, `#065f46` text)
4. Focus rings on interactive form inputs, textareas, and select dropdowns (`ring: 3px solid rgba(16, 185, 129, 0.15)`, border `#10b981`)
5. Active drag-and-drop file upload dropzone border (`border: 2px dashed #34d399`, background `#f0fdf4`)
6. User avatar initials circle background in Sidebar footer (`#ecfdf5` background, `#047857` text)

---

## Visuals & Hierarchy

| Screen | Primary Focal Point | Secondary Visuals | Tertiary Visuals |
|--------|---------------------|-------------------|------------------|
| `/chat` | Bong bóng câu trả lời AI với thẻ trích dẫn pill `[1]` và thanh nhập câu hỏi nổi bật | Danh sách nguồn bằng chứng bên dưới tin nhắn và thumbnail ảnh kỹ thuật | Bảng xem trước bằng chứng trượt (Slide-over Drawer) |
| `/incidents` | Sơ đồ tiến trình `Timeline` sự kiện WMS–TMS của đơn hàng DH001 | Thẻ phân tích nguyên nhân gốc (Root Cause Analysis) và giả thuyết | Form tra cứu mã đơn hàng và danh sách ticket đã xử lý |
| `/reports` | Cụm thẻ chỉ số KPI nổi (Tổng số sự cố, MTTR, Tỷ lệ giải quyết) | Khung xem trước báo cáo HTML/PDF kèm nút "Xuất PDF" | Bộ lọc khoảng ngày/tuần/tháng và bảng danh sách sự cố chi tiết |
| `/datasets` | Bảng danh sách nguồn tài liệu kèm pill badges trạng thái | Khung tải lên kéo thả tài liệu (Dropzone) nét đứt pastel | Hộp thoại phân quyền truy cập chi tiết (DatasetGrantPanel) |
| `/login` | Khung thẻ đăng nhập nổi trắng tinh khôi ở chính giữa với nút "Đăng nhập hệ thống" | Trường nhập Username/Password với focus ring pastel | Logo "Logistics RAG" và nhãn giới thiệu bảo mật |

### Accessibility & Icon Fallbacks
Mọi nút bấm chỉ có icon (Icon-only buttons) bắt buộc phải có thuộc tính `aria-label` và `title` cụ thể:
- Nút đóng Drawer: `aria-label="Đóng bảng xem trước bằng chứng"`
- Nút phóng to ảnh: `aria-label="Phóng to ảnh sơ đồ kỹ thuật"`
- Nút thu nhỏ ảnh: `aria-label="Thu nhỏ ảnh sơ đồ kỹ thuật"`
- Nút đặt lại kích thước ảnh: `aria-label="Đặt lại kích thước ban đầu"`
- Nút đóng Lightbox: `aria-label="Đóng trình xem ảnh"`
- Nút sao chép: `aria-label="Sao chép nội dung câu trả lời"`

---

## Copywriting Contract

| Element | Copy |
|---------|------|
| Primary CTA (Chat) | "Gửi câu hỏi" |
| Primary CTA (Datasets) | "Tải lên tài liệu" |
| Primary CTA (Incidents) | "Phân tích sự cố" |
| Primary CTA (Reports) | "Tạo báo cáo sự cố" |
| Primary CTA (Config) | "Lưu cấu hình mô hình" |
| Primary CTA (Login) | "Đăng nhập hệ thống" |
| Empty state heading (Chat) | "Bắt đầu cuộc hội thoại mới" |
| Empty state body (Chat) | "Đặt câu hỏi về quy trình logistics, tra cứu SOP hoặc sự cố đơn hàng để nhận phân tích kèm bằng chứng trích dẫn." |
| Empty state heading (Datasets) | "Chưa có nguồn tài liệu trong dataset này" |
| Empty state body (Datasets) | "Dataset hiện tại chưa có tài liệu nào được lập chỉ mục. Nhấn 'Tải lên tài liệu' để bắt đầu ingestion dữ liệu vận hành." |
| Empty state heading (Incidents) | "Chưa có sự cố nào được phân tích" |
| Empty state body (Incidents) | "Nhập mã đơn hàng (ví dụ: DH001) hoặc tải file ticket để hệ thống đối chiếu log WMS/TMS và đề xuất hướng xử lý." |
| Empty state heading (Reports) | "Chưa có báo cáo sự cố nào được tạo" |
| Empty state body (Reports) | "Chọn khoảng thời gian hoặc kỳ báo cáo và nhấn 'Tạo báo cáo sự cố' để xem trước số liệu và xuất file PDF." |
| Error state (API / Auth) | "Không thể kết nối đến máy chủ hoặc phiên đăng nhập đã hết hạn. Vui lòng kiểm tra kết nối mạng và đăng nhập lại hệ thống." |
| Error state (Live Scope Recheck) | "Quyền truy cập nguồn tài liệu này đã bị thay đổi hoặc thu hồi. Vui lòng tải lại trang hoặc liên hệ Quản trị viên để cấp quyền." |
| Destructive confirmation (Delete Source) | "Xóa nguồn tài liệu: Bạn có chắc chắn muốn xóa vĩnh viễn nguồn tài liệu này cùng toàn bộ vector chunks liên quan không? Thao tác này không thể hoàn tác." |
| Destructive confirmation (Revoke Grant) | "Thu hồi quyền truy cập: Bạn có chắc chắn muốn hủy quyền truy cập dataset của kỹ thuật viên này không?" |

---

## Registry Safety

| Registry | Blocks Used | Safety Gate |
|----------|-------------|-------------|
| None (Pure CSS & Native React) | Không sử dụng registry bên ngoài | not required |

---

## Checker Sign-Off

- [x] Dimension 1 Copywriting: PASS — Tất cả nhãn CTA cụ thể theo công thức Động từ + Danh từ, các trạng thái Empty/Error có giải pháp xử lý, Destructive confirmation được khai báo đầy đủ.
- [x] Dimension 2 Visuals: PASS — Điểm nhấn tiêu điểm (Focal Points) được xác định rõ ràng cho tất cả các màn hình chính; Icon-only buttons có aria-label đầy đủ.
- [x] Dimension 3 Color: PASS — Tỷ lệ 60/30/10 được phân bổ chuẩn xác, Accent chỉ được dùng cho danh sách thành phần chọn lọc (strict whitelist).
- [x] Dimension 4 Typography: PASS — Khai báo chính xác 4 kích thước font (28, 20, 15, 13) và 2 font weights (400, 600) với tỷ lệ line-height cụ thể.
- [x] Dimension 5 Spacing: PASS — Hệ thống khoảng cách tuân thủ nghiêm ngặt bội số của 4 (4, 8, 16, 24, 32, 48, 64) không có ngoại lệ tùy tiện.
- [x] Dimension 6 Registry Safety: PASS — Dự án sử dụng Pure CSS Variables và Native React 19, không dùng registry bên thứ ba, bảo mật tuyệt đối.

**Approval:** approved 2026-10-15

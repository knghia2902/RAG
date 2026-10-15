# Phase 08: UI Redesign with Pastel Green and White Theme - Context

**Gathered:** 2026-10-15
**Status:** Ready for planning

<domain>
## Phase Boundary

Tái thiết kế toàn bộ giao diện người dùng Web (Frontend) theo phong cách hiện đại, tinh gọn và trang nhã (High-taste Frontend Design), sử dụng tone màu chủ đạo là nền trắng tinh khiết kết hợp nền phụ xám ngọc trai siêu nhẹ (`#ffffff`, `#f8fafc`) và điểm nhấn xanh lá pastel nhẹ dịu / Sage & Mint green (`#10b981`, `#34d399`, `#ecfdf5`, `#f0fdf4`, `#065f46`).

Phạm vi bao phủ toàn bộ các màn hình và components của ứng dụng:
1. Trang Đăng nhập (`/login`)
2. App Shell & Thanh điều hướng Workspace (`Sidebar.tsx`, `Navbar.tsx`, `(workspace)/layout.tsx`)
3. Quản trị Dataset & Nguồn dữ liệu (`/datasets`, `DatasetGrantPanel.tsx`)
4. Hỏi đáp Tri thức & Trích dẫn (`/chat`, `EvidencePreview.tsx`, `ImageLightboxModal.tsx`)
5. Phân tích sự cố logistics (`/incidents`, `Timeline.tsx`)
6. Báo cáo sự cố & Xem trước/Xuất PDF (`/reports`)
7. Cấu hình mô hình AI & Providers (`/configuration`)
8. Quản lý tài khoản & Đổi mật khẩu (`/accounts`, `AccountPanel.tsx`, `/change-password`)

**Ranh giới bất biến (Non-negotiable Guardrails):**
- Bảo toàn 100% logic nghiệp vụ, API client contracts (`lib/contracts.ts`, `lib/api.ts`).
- Giữ vững cơ chế kiểm tra phân quyền thời gian thực (Live Scope Recheck), quyền Admin/Kỹ thuật viên.
- Không phá vỡ kiểm thử backend (244/244 tests) và hoàn thành biên dịch Next.js Turbopack 11 static routes.
</domain>

<decisions>
## Implementation Decisions

### Bố cục Workspace & Điều hướng (Navigation & App Shell)
- **D-01:** Sidebar sáng tinh gọn bên trái: Nền trắng/off-white (`#ffffff`, `#f8fafc`), viền phân cách mỏng mềm mại (`#e2e8f0`), mục menu bo góc mềm (border-radius 8px) với nền hover xanh pastel nhẹ (`#f0fdf4`), mục đang chọn (active) có nền mint pastel (`#ecfdf5`) và chữ xanh lục bảo đậm nét (`#047857`).
- **D-02:** Logo biểu tượng kết hợp: Icon logistics/AI xanh pastel (`#10b981`) kèm tên thương hiệu "Logistics RAG" sắc nét và badge phiên bản "v1.0" nhỏ gọn tinh tế.
- **D-03:** Thẻ người dùng cố định ở chân Sidebar: Avatar tròn chữ cái viết tắt nền xanh pastel, hiển thị tên tài khoản, pill badge vai trò (`Quản trị viên` / `Kỹ thuật viên`) và nút Đăng xuất / Đổi mật khẩu tinh gọn.
- **D-04:** Responsive trên mobile/tablet: Trên màn hình nhỏ (`max-width: 768px`), Sidebar thu gọn thành Off-canvas Drawer trượt êm ái từ cạnh trái khi bấm nút Hamburger, có lớp nền mờ nhẹ (`backdrop-filter: blur(4px)`).

### Hệ thống Design Tokens & Styling (Design System & Color Tokens)
- **D-05:** CSS Variables chuẩn hóa trong `globals.css`: Toàn bộ Design Tokens được định nghĩa tập trung qua các biến CSS (`--bg-app`, `--bg-card`, `--color-pastel-50`, `--color-pastel-100`, `--color-primary-green`, `--color-primary-hover`, `--color-text-main`, `--color-text-muted`, `--border-subtle`, `--shadow-soft`, `--radius-md`). Giữ bundle Next.js siêu nhẹ, thời gian nạp trang tức thì và không cần cài thêm thư viện CSS bên ngoài.
- **D-06:** Sắc độ xanh lá pastel chủ đạo là Sage & Mint Pastel (`#10b981`, `#ecfdf5`, `#f0fdf4`, `#065f46`): Mang lại cảm giác thanh thoát, chuyên nghiệp, dịu mắt cho kỹ thuật viên vận hành liên tục; đảm bảo độ tương phản đạt chuẩn WCAG AA cho văn bản và biểu tượng.
- **D-07:** Modern Clean System Font Stack: Sử dụng hệ font hiện đại trung tính (`-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Inter, sans-serif`) với tỷ lệ giãn dòng thoáng đãng (line-height 1.5 - 1.6), kích thước tiêu chuẩn 15px/16px, font-weight 500/600 cho tiêu đề.
- **D-08:** Soft Elevation & Micro-shadows: Nền thẻ trắng tinh khiết (`#ffffff`) đặt trên nền trang xám ngọc trai (`#f8fafc`), bo góc 12px, viền mỏng tinh tế (`1px solid #e2e8f0` hoặc viền nhấn nhẹ `#d1fae5`), kết hợp đổ bóng vi mô hai lớp tự nhiên (`box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.05), 0 1px 2px 0 rgba(0, 0, 0, 0.03)`).

### Trải nghiệm Hội thoại & Trích dẫn (Chat, Evidence & Lightbox)
- **D-09:** Bong bóng tin nhắn bo góc mềm: Tin nhắn Kỹ thuật viên (User) có nền xanh mint pastel (`#ecfdf5`), viền mỏng (`#a7f3d0`), bo góc lớn 16px (góc dưới phải 4px) đặt lệch phải; Tin nhắn Trợ lý AI có nền trắng tinh khiết (`#ffffff`), viền mỏng (`#e2e8f0`), đổ bóng nhẹ lệch trái, kèm avatar AI xanh pastel tròn.
- **D-10:** Pill Badge tương tác pastel: Số trích dẫn `[1]`, `[2]` dạng viên thuốc nhỏ màu mint pastel (`#d1fae5`), chữ xanh đậm (`#065f46`), hiệu ứng hover nhấc nhẹ; danh sách nguồn bằng chứng bên dưới dạng thẻ mini bo góc kèm icon định dạng tài liệu (PDF, DOCX, LOG).
- **D-11:** Bảng xem trước bằng chứng `EvidencePreview`: Thiết kế dạng Slide-over Drawer trượt mượt mà từ cạnh phải (~480px) có nền mờ nhẹ, giúp kỹ thuật viên vừa đối chiếu nguồn tài liệu vừa theo dõi dòng chat mà không bị che khuất ngữ cảnh.
- **D-12:** Trình xem ảnh kỹ thuật `ImageLightboxModal`: Thumbnail ảnh trích dẫn bo góc 12px viền pastel; modal xem ảnh chi tiết có thanh công cụ nổi dạng Floating dock ở mép dưới (Zoom in/out, Reset, Đóng) với nền kính mờ glassmorphism trên phông tối mờ sâu (`rgba(15, 23, 42, 0.8)`).

### Trình bày Dữ liệu, Báo cáo & Thẻ chỉ số (Tables, KPI Cards & Controls)
- **D-13:** Bảng dữ liệu danh sách thanh lịch tối giản: Tiêu đề cột chữ xám thanh thoát (`#64748b`), đường phân cách hàng siêu mỏng (`#f1f5f9`), hiệu ứng hover cả hàng chuyển sang nền xanh mint nhạt (`#f0fdf4`), khoảng đệm hàng thoáng đãng (padding 14px-16px).
- **D-14:** Thẻ KPI nổi với icon pastel: Con số chính hiển thị lớn đậm (28px-32px), nhãn chỉ số thanh lịch, icon minh họa bo tròn nền xanh mint pastel (`#ecfdf5`) ở góc trên, viền thẻ mỏng tinh tế.
- **D-15:** Soft Pastel Pill Badges: Huy hiệu trạng thái hình viên thuốc bo tròn hoàn toàn (`border-radius: 9999px`) với màu nền pastel êm mắt và chữ cùng tông đậm: Xanh lá mint (`#ecfdf5`, `#047857`) cho "Ready/Resolved/Low", Vàng hổ phách pastel (`#fffbeb`, `#b45309`) cho "Indexing/Medium", Đỏ hồng pastel (`#fef2f2`, `#b91c1c`) cho "Failed/P1 Critical", Xám nhạt (`#f1f5f9`, `#475569`) cho "Pending".
- **D-16:** Nút bấm và Form controls hiện đại: Nút chính (Primary) màu xanh pastel đậm nét (`#10b981` -> hover `#059669`), nút phụ nền trắng viền xám mỏng; Ô nhập liệu focus có viền xanh mint kèm vòng phát sáng êm (`ring 3px rgba(16, 185, 129, 0.15)`); Khung kéo thả file (Dropzone) viền đứt nét xanh mint nền pastel (`#f0fdf4`).

### the agent's Discretion
- Chi tiết animation transitions (150ms - 200ms ease-in-out).
- Tinh chỉnh icon SVG inline (Lucide-style hoặc Heroicons-style tối giản) cho các nút hành động (Copy, Download, Zoom, Close, Refresh, Trash).
- Bố cục responsive chi tiết cho từng bảng dữ liệu trên tablet và mobile.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Frontend Core & Design System
- `frontend/src/app/globals.css` — Nơi định nghĩa toàn bộ Design Tokens và CSS classes chung.
- `frontend/src/components/Sidebar.tsx` — Component điều hướng chính và hiển thị tài khoản/vai trò.
- `frontend/src/app/(workspace)/layout.tsx` — Bố cục App Shell chung cho toàn bộ workspace.

### Core Feature Pages
- `frontend/src/app/(workspace)/chat/page.tsx` — Giao diện hỏi đáp tri thức, bong bóng chat, trích dẫn.
- `frontend/src/app/(workspace)/datasets/page.tsx` — Quản trị dataset, danh sách nguồn, tiến trình ingestion.
- `frontend/src/app/(workspace)/incidents/page.tsx` — Phân tích sự cố logistics, tra cứu DH001, timeline.
- `frontend/src/app/(workspace)/reports/page.tsx` — Thẻ chỉ số KPI sự cố, lọc thời gian, preview báo cáo.
- `frontend/src/app/(workspace)/configuration/page.tsx` — Cấu hình model & providers.
- `frontend/src/app/login/page.tsx` — Màn hình đăng nhập phong cách pastel green & white.

### Specialized UI Components
- `frontend/src/components/EvidencePreview.tsx` — Slide-over Drawer xem trích dẫn và ảnh nguồn.
- `frontend/src/components/ImageLightboxModal.tsx` — Trình xem phóng to ảnh sơ đồ/kỹ thuật với Floating dock.
- `frontend/src/components/Timeline.tsx` — Trình tự chuỗi sự kiện đồng bộ WMS-TMS cho sự cố logistics.
- `frontend/src/components/DatasetGrantPanel.tsx` — Hộp thoại phân quyền dataset chi tiết.
- `frontend/src/components/AccountPanel.tsx` — Quản trị danh sách người dùng và cấp quyền.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `frontend/src/hooks/use-session.ts` — Quản lý phiên làm việc, JWT token, vai trò và thông tin người dùng.
- `frontend/src/lib/api.ts` — Toàn bộ HTTP client functions gọi FastAPI backend kèm xử lý lỗi và token injection.
- `frontend/src/lib/contracts.ts` — Type definitions hoàn chỉnh cho datasets, chat, incidents, reports, models.

### Established Patterns
- Client Components (`"use client"`) cho tất cả các trang tương tác trạng thái.
- Phân quyền giao diện theo role: `user.role === 'admin'` hiển thị các mục quản trị (Datasets upload, Configuration, Accounts); kỹ thuật viên chỉ xem trong phạm vi được cấp quyền.
- Tải dữ liệu bất đồng bộ với trạng thái loading, empty states và error banners rõ ràng.

### Integration Points
- `globals.css` là điểm kết nối phong cách trung tâm — nâng cấp CSS Variables tại đây sẽ tự động lan tỏa tới toàn bộ ứng dụng.
- Bố cục App Shell trong `(workspace)/layout.tsx` và `Sidebar.tsx` định hình toàn bộ trải nghiệm điều hướng.

</code_context>

<specifics>
## Specific Ideas

- **Giao diện sáng sủa, trang nhã:** Tránh hoàn toàn phong cách tối thô ráp (dark clunky theme) hoặc màu xanh dương kỹ thuật quá bão hòa. Ưu tiên nền trắng tinh, xám ngọc trai, điểm xuyết màu xanh lá ngọc bích / mint pastel nhẹ nhàng, thanh thoát.
- **Trải nghiệm kiểm tra bằng chứng mượt mà:** Kỹ thuật viên khi click vào số trích dẫn `[1]` hoặc thumbnail ảnh trong chat có thể mở ngay Drawer xem nguồn hoặc phóng to sơ đồ kỹ thuật mà không làm mất dòng suy nghĩ trong hội thoại.

</specifics>

<deferred>
## Deferred Ideas

None — thảo luận tập trung 100% vào phạm vi tái thiết kế giao diện Phase 8.

</deferred>

---

*Phase: 08-ui-redesign-with-pastel-green-and-white-theme*
*Context gathered: 2026-10-15*

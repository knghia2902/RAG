# Phase 5: On-Demand Incident Reports and PDF - Context

**Gathered:** 2026-10-14
**Status:** Ready for planning

<domain>
## Phase Boundary

Cung cấp tính năng tạo báo cáo sự cố IT kết hợp hệ thống logistics theo yêu cầu (on-demand) theo kỳ ngày, tuần, tháng hoặc khoảng thời gian tùy chọn trong phạm vi dataset được cấp quyền. Báo cáo tổng hợp số liệu thống kê tất định (tổng số ticket/incident, phân loại nhóm lỗi, mức độ ưu tiên, hệ thống ảnh hưởng, thời gian xử lý MTTR, lỗi lặp lại) kết hợp nhận định xu hướng và khuyến nghị hành động của LLM có trích dẫn nguồn bằng chứng. Cho phép xem trước trên giao diện Web, kiểm tra snapshot/phiên bản nguồn và tải tệp PDF tiếng Việt chuẩn in ấn với xử lý ngắt trang bảng biểu chuyên nghiệp. Bảo vệ quyền truy cập theo thời gian thực (Live Scope Recheck: HTTP 403 Forbidden khi bị thu hồi quyền). Không bao gồm lập lịch tự động (scheduler) hay xuất file Excel/Word trong MVP.

</domain>

<decisions>
## Implementation Decisions

### 1. Biên kỳ thời gian & Quy tắc tính toán số liệu thống kê (Timezone & Deterministic Metrics - REP-01, REP-02)
- **D-01 (Timezone & Boundary):** Cố định múi giờ chuẩn Việt Nam `Asia/Ho_Chi_Minh` (UTC+7). Mọi kỳ báo cáo (Hôm nay, Tuần này, Tháng này, hoặc Tùy chọn) xác định biên từ `00:00:00` đến `23:59:59.999999` (UTC+7), quy đổi về UTC khi truy vấn SQL. Múi giờ UTC+7 và khoảng thời gian chính xác được hiển thị rõ ràng trên tiêu đề báo cáo.
- **D-02 (MTTR & Open Incidents):** Chỉ tính thời gian giải quyết trung bình (MTTR / Mean Time To Resolve) cho các ticket và incident đã hoàn tất (`is_resolved=True` hoặc có `resolved_at`). Các sự cố chưa đóng hiển thị trạng thái "Đang mở" và thời gian xử lý hiển thị rõ ràng là "Chưa hoàn tất", tuyệt đối không giả định hay ước lượng thời gian xử lý theo tiêu chuẩn REP-03.

### 2. Gom nhóm lỗi lặp lại & Tích hợp nhận định AI (Recurring Error Grouping & AI Narrative Synthesizer - REP-03, REP-04)
- **D-03 (Recurring Error Rule):** Gom nhóm tất định theo cặp `[Hệ thống + Mã lỗi/Nhóm lỗi]` (ví dụ: `API_GATEWAY + 504_GATEWAY_TIMEOUT`, `WMS + SYNC_PAYLOAD_MISMATCH`, `TMS + DISPATCH_TIMEOUT`). Bất kỳ lỗi nào xuất hiện từ 2 lần trở lên (`>= 2`) trong kỳ báo cáo sẽ tự động được đánh dấu là "Lỗi lặp lại" kèm tần suất, tỷ lệ và danh sách mã đơn hàng/ticket liên quan.
- **D-04 (Deterministic Metrics vs LLM Separation):** Tách bạch triệt để: toàn bộ số liệu thống kê (tổng ticket, incident, phân bổ hệ thống, mức ưu tiên, MTTR, tần suất lỗi lặp) do SQL/Python tính toán tất định 100% từ bảng `incident_analyses` và `canonical_records`, tuyệt đối không tính từ top-k retrieval context. LLM chỉ đóng vai trò sinh phần "Nhận định xu hướng" và "Khuyến nghị hành động theo SOP" có trích dẫn nguồn. Nếu LLM gặp sự cố hoặc timeout, hệ thống vẫn xuất đầy đủ bảng biểu số liệu xác định kèm thông báo cảnh báo trực quan theo SYS-05.

### 3. Trải nghiệm xem trước báo cáo & Tra cứu bằng chứng nguồn (Report Preview & Provenance Inspection - REP-05, REP-06, AUTH-04)
- **D-05 (Report Persistence & Live Scope Recheck):** Tạo bảng ORM `reports` lưu trữ `account_id`, `title`, `period_type`, `start_time`, `end_time`, `dataset_ids` (mảng UUID các dataset tham chiếu), `metrics_json` (số liệu KPI tất định), `narrative_json` (nhận định của LLM), `provenance_json` (danh sách tệp nguồn, source version). Thực thi Live Scope Recheck (D-05, AUTH-04): khi người dùng mở lại báo cáo cũ hoặc tải PDF, backend kiểm tra quyền truy cập đối với tất cả các `dataset_ids`; nếu quyền bị thu hồi, lập tức trả về HTTP 403 Forbidden.
- **D-06 (Two-Tab UI & Preview Dashboard):** Màn hình `/reports` thiết kế bố cục tab kép:
  - Tab 1: "Tạo báo cáo mới" (bộ chọn kỳ nhanh Hôm nay / Tuần này / Tháng này / Tùy chọn ngày; bộ lọc Dataset).
  - Tab 2: "Lịch sử báo cáo" (danh sách báo cáo đã tạo, thời điểm tạo, kỳ báo cáo, trạng thái, nút Xem trước và Tải PDF).
  - Màn hình Xem trước hiển thị Dashboard chuyên sâu với thẻ KPI tổng quan, bảng phân loại hệ thống/ưu tiên, bảng lỗi lặp lại, khối nhận định của AI và modal tra cứu đoạn trích nguồn gốc (Provenance Modal).

### 4. Định dạng PDF & Xử lý ngắt trang font tiếng Việt (PDF Generation & Multi-page Table Layout - REP-06)
- **D-07 (WeasyPrint & Local Vietnamese Fonts):** Sử dụng WeasyPrint biên dịch từ mẫu template HTML/CSS Jinja2 do backend kiểm soát, nhúng bộ font tiếng Việt (`Noto Sans` / `Liberation Sans`) đóng gói cục bộ trong container Docker, định dạng khổ giấy A4 dọc (Portrait) thanh lịch, chuẩn mực doanh nghiệp.
- **D-08 (Professional Pagination & Multi-Page Tables):** Áp dụng quy tắc in ấn CSS `@page`: lặp lại `thead` (`display: table-header-group`) ở đầu mỗi trang mới khi bảng biểu kéo dài nhiều trang; áp dụng `page-break-inside: avoid` trên từng hàng `tr` để không bị cắt đôi dòng; chân trang hiển thị số trang `Trang counter(page) / counter(pages)` kèm mã báo cáo, người tạo và thời gian xuất theo múi giờ UTC+7.

### the agent's Discretion
- Thiết kế chi tiết template HTML/CSS Jinja2 cho WeasyPrint.
- Bảng màu và kiểu dáng thẻ KPI (Cards) trong Dashboard Web và PDF.
- Chi tiết câu lệnh SQL aggregation để tính toán các số liệu nhóm lỗi, hệ thống, mức độ ưu tiên.
- Quản lý bộ đệm PDF tạm thời hoặc sinh luồng trực tiếp (StreamingResponse) khi người dùng nhấn tải PDF.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Architecture and Stack Specifications
- `.planning/research/ARCHITECTURE.md` — Cấu trúc Report Service, module reports, và quy tắc cách ly LLM Provider
- `.planning/research/STACK.md` — Đặc tả WeasyPrint 70.0, Jinja2 template engine và font tiếng Việt local
- `.planning/REQUIREMENTS.md` § On-Demand Reporting — Đặc tả chi tiết các yêu cầu REP-01 đến REP-06, AUTH-04, SYS-05

### Precedent Context & Data Contracts
- `.planning/phases/04-logistics-incident-and-ticket-analysis/04-CONTEXT.md` — Quyết định cấu trúc `IncidentAnalysis`, phân loại lỗi và trích dẫn SOP
- `backend/app/database/models.py` — Khai báo các mô hình dữ liệu hiện tại (`IncidentAnalysis`, `CanonicalRecord`, `SourceVersion`)
- `data/sample/logistics_incidents/` — Bộ dữ liệu mẫu WMS, TMS, API Gateway và tickets phục vụ thống kê báo cáo

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `IncidentAnalysis` ORM model (`backend/app/database/models.py`): Chứa toàn bộ ca phân tích sự cố đã thực hiện, làm nguồn số liệu cho báo cáo.
- `CanonicalRecord` ORM model: Chứa các bản ghi log và ticket đã ingestion trong kỳ.
- `allowed_dataset_ids` dependency (`backend/app/api/auth.py`): Dùng để lọc phạm vi dữ liệu và thực thi Live Scope Recheck.
- `mask_secrets` filter (`backend/app/rag/secret_filter.py`): Làm sạch context trước khi gửi đến LLM narrative synthesizer.
- Badge components & màu sắc hệ thống (`frontend/src/components/Timeline.tsx`): Tái sử dụng bảng màu hệ thống (WMS Xanh lam, API Tím, TMS Cam, v.v.).

### Established Patterns
- Live Scope Recheck: Kiểm tra quyền dataset thời gian thực trước khi trả về chi tiết hoặc tệp đính kèm, ném HTTP 403 Forbidden nếu quyền bị thu hồi.
- Pydantic V2 DTOs: Sử dụng `model_config = ConfigDict(extra="forbid", frozen=True)` cho các hợp đồng dữ liệu.
- Next.js Turbopack: Tạo trang tĩnh / dynamic route với App Router tại `frontend/src/app/(workspace)/reports/`.

### Integration Points
- Backend Service: `backend/app/modules/reports/service.py`, `backend/app/modules/reports/pdf_generator.py`
- Backend Router: `backend/app/api/reports.py` đăng ký vào `backend/app/main.py` tại `/api/v1/reports`
- Database Migration: `backend/alembic/versions/0005_incident_reports.py` tạo bảng `reports`
- Frontend Page: `frontend/src/app/(workspace)/reports/page.tsx` và liên kết trong `frontend/src/components/Sidebar.tsx`

</code_context>

<specifics>
## Specific Ideas

- Báo cáo cần mang phong cách báo cáo quản trị kỹ thuật chuẩn mực: Đầu trang có logo/tiêu đề "BÁO CÁO SỰ CỐ HỆ THỐNG IT & LOGISTICS", thông tin kỳ báo cáo và thời điểm xuất.
- Khối số liệu KPI nên hiển thị dạng thẻ card nổi bật (Tổng số sự cố, Tổng số ticket, Tỷ lệ lỗi lặp lại, MTTR trung bình).
- Bảng lỗi lặp lại cần chỉ rõ số lần xuất hiện và liên kết tới các mã đơn hàng bị ảnh hưởng.
- Tải PDF nhanh chóng với tên file chuẩn hóa: `Bao_cao_su_co_[Period]_[Date].pdf`.

</specifics>

<deferred>
## Deferred Ideas

- Scheduler tự động tạo báo cáo định kỳ (hàng ngày lúc 08:00 hoặc thứ Hai đầu tuần) và gửi qua Email/Slack (dành cho v2 - EXT-02).
- Xuất báo cáo sang tệp Excel đa sheet (.xlsx) hoặc Word (.docx) (dành cho v2 - EXT-05).
- Tích hợp biểu đồ động dạng đồ thị tròn/cột tương tác sâu hơn (Chart.js / Recharts) trên web.

</deferred>

---

*Phase: 05-on-demand-incident-reports-and-pdf*
*Context gathered: 2026-10-14*

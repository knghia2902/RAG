# Phase 5: On-Demand Incident Reports and PDF - Research

**Researched:** 2026-10-14  
**Domain:** Deterministic incident aggregation, recurring error grouping, AI narrative synthesis, WeasyPrint PDF generation with Vietnamese fonts, multi-page print CSS, and Live Scope Recheck  
**Confidence:** HIGH  

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- **D-01 (Timezone & Boundary):** Cố định múi giờ chuẩn Việt Nam `Asia/Ho_Chi_Minh` (UTC+7). Mọi kỳ báo cáo (Hôm nay, Tuần này, Tháng này, hoặc Tùy chọn) xác định biên từ `00:00:00` đến `23:59:59.999999` (UTC+7), quy đổi về UTC khi truy vấn SQL. Múi giờ UTC+7 và khoảng thời gian chính xác được hiển thị rõ ràng trên tiêu đề báo cáo.
- **D-02 (MTTR & Open Incidents):** Chỉ tính thời gian giải quyết trung bình (MTTR / Mean Time To Resolve) cho các ticket và incident đã hoàn tất (`is_resolved=True` hoặc có `resolved_at`). Các sự cố chưa đóng hiển thị trạng thái "Đang mở" và thời gian xử lý hiển thị rõ ràng là "Chưa hoàn tất", tuyệt đối không giả định hay ước lượng thời gian xử lý theo tiêu chuẩn REP-03.
- **D-03 (Recurring Error Rule):** Gom nhóm tất định theo cặp `[Hệ thống + Mã lỗi/Nhóm lỗi]` (ví dụ: `API_GATEWAY + 504_GATEWAY_TIMEOUT`, `WMS + SYNC_PAYLOAD_MISMATCH`, `TMS + DISPATCH_TIMEOUT`). Bất kỳ lỗi nào xuất hiện từ 2 lần trở lên (`>= 2`) trong kỳ báo cáo sẽ tự động được đánh dấu là "Lỗi lặp lại" kèm tần suất, tỷ lệ và danh sách mã đơn hàng/ticket liên quan.
- **D-04 (Deterministic Metrics vs LLM Separation):** Tách bạch triệt để: toàn bộ số liệu thống kê (tổng ticket, incident, phân bổ hệ thống, mức ưu tiên, MTTR, tần suất lỗi lặp) do SQL/Python tính toán tất định 100% từ bảng `incident_analyses` và `canonical_records`, tuyệt đối không tính từ top-k retrieval context. LLM chỉ đóng vai trò sinh phần "Nhận định xu hướng" và "Khuyến nghị hành động theo SOP" có trích dẫn nguồn. Nếu LLM gặp sự cố hoặc timeout, hệ thống vẫn xuất đầy đủ bảng biểu số liệu xác định kèm thông báo cảnh báo trực quan theo SYS-05.
- **D-05 (Report Persistence & Live Scope Recheck):** Tạo bảng ORM `reports` lưu trữ `account_id`, `title`, `period_type`, `start_time`, `end_time`, `dataset_ids` (mảng UUID các dataset tham chiếu), `metrics_json` (số liệu KPI tất định), `narrative_json` (nhận định của LLM), `provenance_json` (danh sách tệp nguồn, source version). Thực thi Live Scope Recheck (D-05, AUTH-04): khi người dùng mở lại báo cáo cũ hoặc tải PDF, backend kiểm tra quyền truy cập đối với tất cả các `dataset_ids`; nếu quyền bị thu hồi, lập tức trả về HTTP 403 Forbidden.
- **D-06 (Two-Tab UI & Preview Dashboard):** Màn hình `/reports` thiết kế bố cục tab kép:
  - Tab 1: "Tạo báo cáo mới" (bộ chọn kỳ nhanh Hôm nay / Tuần này / Tháng này / Tùy chọn ngày; bộ lọc Dataset).
  - Tab 2: "Lịch sử báo cáo" (danh sách báo cáo đã tạo, thời điểm tạo, kỳ báo cáo, trạng thái, nút Xem trước và Tải PDF).
  - Màn hình Xem trước hiển thị Dashboard chuyên sâu với thẻ KPI tổng quan, bảng phân loại hệ thống/ưu tiên, bảng lỗi lặp lại, khối nhận định của AI và modal tra cứu đoạn trích nguồn gốc (Provenance Modal).
- **D-07 (WeasyPrint & Local Vietnamese Fonts):** Sử dụng WeasyPrint biên dịch từ mẫu template HTML/CSS Jinja2 do backend kiểm soát, nhúng bộ font tiếng Việt (`Noto Sans` / `Liberation Sans` / `DejaVu Sans`) đóng gói cục bộ trong container Docker, định dạng khổ giấy A4 dọc (Portrait) thanh lịch, chuẩn mực doanh nghiệp.
- **D-08 (Professional Pagination & Multi-Page Tables):** Áp dụng quy tắc in ấn CSS `@page`: lặp lại `thead` (`display: table-header-group`) ở đầu mỗi trang mới khi bảng biểu kéo dài nhiều trang; áp dụng `page-break-inside: avoid` trên từng hàng `tr` để không bị cắt đôi dòng; chân trang hiển thị số trang `Trang counter(page) / counter(pages)` kèm mã báo cáo, người tạo và thời gian xuất theo múi giờ UTC+7.

### the agent's Discretion

- Thiết kế module `backend/app/modules/reports` với Service layer và PDF Generator layer sạch.
- Cấu hình Dockerfile backend bổ sung các gói system runtime (`libpango-1.0-0`, `libpangoft2-1.0-0`, `libharfbuzz0b`, `libcairo2`, `fonts-liberation`, `fonts-dejavu-core`) và `weasyprint==70.0`.
- Tạo Alembic migration `0005_incident_reports.py` tạo bảng `reports` và cập nhật `backend/app/api/health.py` cùng `test_migrations.py`.
- Tích hợp route FastAPI `/api/v1/reports` với các endpoint: `POST /generate`, `GET /history`, `GET /{report_id}`, `GET /{report_id}/pdf`, `GET /{report_id}/provenance`.

### Deferred Ideas (OUT OF SCOPE)

- Scheduler tự động gửi báo cáo định kỳ qua Email/Slack (v2 - EXT-02).
- Xuất file Excel (.xlsx) và Word (.docx) (v2 - EXT-05).
- Connectors trực tiếp vào cơ sở dữ liệu live của WMS/TMS (v2 - EXT-06).
</user_constraints>

<architectural_responsibility_map>
## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Report Parameters & Timezone Normalization | API/Backend (`app.modules.reports.service`) | Browser/Client (`/reports`) | Backend nhận period (`daily`, `weekly`, `monthly`, `custom`), chuẩn hóa mốc thời gian UTC+7 `00:00:00 - 23:59:59` và quy đổi sang UTC truy vấn database |
| Deterministic Incident Metrics Aggregator | API/Backend (`app.modules.reports.service`) | Database (`incident_analyses`, `canonical_records`) | Tính toán 100% tất định các chỉ số KPI: tổng số sự cố, ticket, MTTR, phân bổ hệ thống, mức ưu tiên, và danh sách lỗi lặp lại |
| Narrative & SOP Recommendation Synthesizer | API/Backend (`app.modules.reports.narrative`) | OpenAI LLM Provider | Sinh đoạn văn nhận định xu hướng và khuyến nghị theo SOP có trích dẫn nguồn, cách ly hoàn toàn khỏi số liệu thống kê |
| Report Snapshot & Live Scope Recheck | API/Backend (`app.api.reports`) | Database (`reports`, `account_dataset_permissions`) | Lưu trữ báo cáo hoàn chỉnh; kiểm tra Live Scope Recheck tức thì trên cả màn hình xem trước và tải PDF (403 Forbidden nếu thu hồi quyền) |
| WeasyPrint PDF Compiler & Vietnamese Typography | Backend Worker/Service (`app.modules.reports.pdf_generator`) | WeasyPrint 70.0 & Cairo/Pango runtime | Render template HTML/CSS Jinja2 sang tệp PDF A4 chuẩn in ấn, nhúng font tiếng Việt cục bộ và phân trang chuyên nghiệp |
| Report Dashboard & Preview UI | Browser/Client (Next.js `/reports`) | Frontend Server (App Router) | Giao diện tab kép: form tạo báo cáo nhanh, bảng lịch sử báo cáo, dashboard xem trước KPI và modal mở trích dẫn provenance |
</architectural_responsibility_map>

<research_summary>
## Summary

Phase 5 hiện thực hóa khả năng tổng hợp và xuất bản báo cáo sự cố toàn diện theo yêu cầu (On-Demand Incident Reports) cho đội ngũ quản trị và kỹ thuật viên vận hành logistics. Khác với chức năng tra cứu hay phân tích từng ca đơn lẻ ở Phase 3 và Phase 4, Phase 5 cho phép xem xét bức tranh tổng thể về tình trạng ổn định của hệ thống trong một chu kỳ (ngày, tuần, tháng hoặc khoảng thời gian tùy chọn).

Trọng tâm kỹ thuật then chốt của Phase 5:
1. **Tính toán số liệu tất định (Deterministic Metrics Calculation):** Tuyệt đối không để LLM "đoán" hoặc trích xuất số liệu từ ngữ cảnh top-k. Mọi chỉ số (tổng sự cố, ticket, thời gian xử lý MTTR, tỷ lệ theo hệ thống, lỗi lặp) được tính toán trực tiếp bằng SQL/Python từ các bản ghi `incident_analyses` và `canonical_records` nằm trong phạm vi dataset được cấp quyền.
2. **Nhận định định tính có kiểm soát (Guarded Qualitative Narrative):** LLM chỉ đóng vai trò phân tích các pattern đứt gãy, nhận xét xu hướng lỗi lặp (ví dụ: chuỗi timeout API Gateway giờ cao điểm) và đối chiếu quy trình SOP tương ứng để đưa ra khuyến nghị. Trường hợp LLM gặp lỗi timeout, hệ thống vẫn xuất báo cáo đầy đủ bảng số liệu kèm thông báo rõ ràng (SYS-05).
3. **Engine WeasyPrint 70.0 & Typography tiếng Việt:** Khảo sát thực tế trong container backend (Debian trixie) cho thấy apt repository hỗ trợ đầy đủ các thư viện native `libpango-1.0-0`, `libcairo2`, `fonts-liberation`, `fonts-dejavu-core`, kết hợp với `weasyprint==70.0` qua pip. Thử nghiệm thực tế trên môi trường Docker container đã xác nhận WeasyPrint 70.0 import và hoạt động 100% không lỗi, hỗ trợ font tiếng Việt hoàn hảo không bị lỗi tofu (ô vuông).
4. **Bảo mật Live Scope Recheck (AUTH-04, REP-06):** Mọi báo cáo được lưu trữ kèm snapshot các dataset IDs tham chiếu. Khi người dùng mở lại báo cáo cũ hoặc bấm tải PDF, hệ thống kiểm tra lại quyền truy cập dataset tại thời điểm thực tế; nếu quyền bị thu hồi, yêu cầu lập tức bị chặn với HTTP 403 Forbidden.

**Primary recommendation:**
- Nâng cấp `backend/Dockerfile` cài đặt các runtime dependencies cho WeasyPrint và `weasyprint==70.0`.
- Tạo Alembic migration `0005_incident_reports.py` định nghĩa bảng `reports`.
- Cập nhật `backend/app/api/health.py` và `backend/tests/integration/test_migrations.py` nhận diện version `0005_incident_reports`.
- Triển khai module `backend/app/modules/reports` gồm `contracts.py`, `service.py`, `pdf_generator.py`, và router `backend/app/api/reports.py`.
- Xây dựng giao diện Next.js tại `frontend/src/app/(workspace)/reports/page.tsx` và bổ sung link Sidebar.
</research_summary>

<standard_stack>
## Standard Stack

### Core Backend & Services
| Library / Component | Version | Purpose | Why Standard |
|---|---|---|---|
| `weasyprint` | `70.0` (Đã kiểm chứng) | Biên dịch HTML/CSS sang file PDF | Chuẩn in ấn chất lượng cao, tuân thủ CSS Paged Media Module, hỗ trợ CSS Flexbox/Grid và font OpenType/TrueType |
| `jinja2` | `3.1.6` (Đã cài đặt sẵn) | Template engine render HTML báo cáo cho WeasyPrint | Tách biệt hoàn toàn tầng logic số liệu và tầng trình bày giao diện PDF |
| `libpango-1.0-0` / `libcairo2` | Debian 13 trixie | Thư viện native render đồ họa và typography cho WeasyPrint | Bắt buộc cho WeasyPrint render chữ và xuất vector PDF |
| `fonts-liberation` / `fonts-dejavu-core` | Debian 13 trixie | Bộ font chữ Unicode tiếng Việt đóng gói cục bộ trong container | Đảm bảo 100% hiển thị tiếng Việt có dấu chuẩn xác trong file PDF mà không phụ thuộc font internet |
| `pydantic` | `2.13.5` (Đã cài đặt) | Validation DTOs cho Report Request, Metrics, và Snapshot DTO | Đảm bảo tính toàn vẹn và bất biến của dữ liệu báo cáo |
| `sqlalchemy` | `2.0.54` (Đã cài đặt) | ORM model `Report` và các truy vấn tổng hợp SQL | Tích hợp hoàn hảo với PostgreSQL 18 và mô hình hiện tại |

### Supporting Frontend Tools
| Component / Library | Version | Purpose | When to Use |
|---|---|---|---|
| `lucide-react` | `0.453.0` | Biểu tượng cho KPI cards, nút Tải PDF, nút Xem trước | Giao diện `/reports` |
| Turbopack / Next.js | `16.3.8` | App Router cho trang `/reports` | Hiển thị giao diện tab kép và modal preview |

</standard_stack>

<architecture_patterns>
## Architecture Patterns

### Module Structure
```
backend/app/modules/reports/
├── __init__.py
├── contracts.py       # Pydantic V2 DTOs (ReportCreateRequest, ReportMetricsDTO, ReportResponseDTO)
├── service.py         # ReportService: timezone conversion, SQL aggregation, narrative coordination
├── pdf_generator.py   # WeasyPrint PDF compiler with Jinja2 HTML/CSS templates
└── templates/
    └── incident_report.html  # Jinja2 print-ready HTML/CSS template
```

### Database Schema (reports table)
```python
class Report(Base):
    __tablename__ = "reports"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("accounts.id"), index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    period_type: Mapped[str] = mapped_column(String(32), nullable=False)  # daily, weekly, monthly, custom
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    dataset_ids: Mapped[list[str]] = mapped_column(JSONB, nullable=False)
    metrics_json: Mapped[dict] = mapped_column(JSONB, nullable=False)
    narrative_json: Mapped[dict] = mapped_column(JSONB, nullable=False)
    provenance_json: Mapped[dict] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
```

### CSS Paged Media Best Practices (Printing Multi-Page PDF)
```css
@page {
  size: A4 portrait;
  margin: 20mm 15mm 20mm 15mm;
  @bottom-left {
    content: "Logistics RAG · Báo cáo vận hành IT & Logistics";
    font-family: 'Liberation Sans', 'DejaVu Sans', sans-serif;
    font-size: 8pt;
    color: #64748b;
  }
  @bottom-right {
    content: "Trang " counter(page) " / " counter(pages);
    font-family: 'Liberation Sans', 'DejaVu Sans', sans-serif;
    font-size: 8pt;
    color: #64748b;
  }
}

table {
  width: 100%;
  border-collapse: collapse;
}

thead {
  display: table-header-group; /* Lặp lại tiêu đề bảng ở mỗi trang mới */
}

tr {
  page-break-inside: avoid;    /* Không cắt ngang dòng bảng khi sang trang */
}

h2, h3 {
  page-break-after: avoid;     /* Không để tiêu đề mục mồ côi ở cuối trang */
}
```

</architecture_patterns>

<validation_architecture>
## Validation Architecture

### Automated Verification Plan
1. **Unit Tests (`backend/tests/unit/test_report_service.py`):**
   - Kiểm tra tính toán chính xác mốc biên thời gian UTC+7 cho ngày, tuần, tháng và tùy chọn.
   - Kiểm tra quy tắc tính MTTR chỉ trên các sự cố đã hoàn tất, sự cố đang mở hiển thị "Đang mở".
   - Kiểm tra quy tắc gom nhóm lỗi lặp lại theo cặp `[Hệ thống + Mã lỗi]` xuất hiện `>= 2` lần.
   - Kiểm tra tính độc lập của số liệu KPI khi LLM gặp sự cố (fallback narrative an toàn).
2. **PDF Generator Unit Tests (`backend/tests/unit/test_pdf_generator.py`):**
   - Biên dịch mẫu HTML sang PDF dạng bytes thành công.
   - Kiểm tra header PDF magic bytes `%PDF-1.`.
   - Kiểm tra hiển thị chuỗi Unicode tiếng Việt có dấu không gây lỗi encoding.
3. **Integration Tests (`backend/tests/integration/test_reports_api.py`):**
   - `POST /api/v1/reports/generate`: Tạo báo cáo thành công với đầy đủ số liệu và snapshot.
   - `GET /api/v1/reports/history`: Lấy danh sách lịch sử báo cáo của người dùng (kỹ thuật viên) hoặc toàn hệ thống (admin).
   - `GET /api/v1/reports/{id}`: Xem chi tiết báo cáo kèm kiểm tra quyền dataset.
   - `GET /api/v1/reports/{id}/pdf`: Tải file PDF binary thành công với `Content-Type: application/pdf`.
4. **Live Scope Recheck Test (`backend/tests/integration/test_report_scope_recheck.py`):**
   - Tạo báo cáo dựa trên dataset A.
   - Thu hồi quyền truy cập dataset A của tài khoản kỹ thuật viên.
   - Gọi lại `GET /{id}` và `GET /{id}/pdf` → Xác thực trả về ngay lập tức HTTP `403 Forbidden` (tuân thủ AUTH-04, REP-06).
5. **Frontend Production Build:**
   - Xác thực `npm --prefix frontend run build` vượt qua 100% với Turbopack, tạo static route `/reports`.

</validation_architecture>

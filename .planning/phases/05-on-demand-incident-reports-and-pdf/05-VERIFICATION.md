---
phase: 05-on-demand-incident-reports-and-pdf
verified: 2026-10-14T15:58:00+07:00
status: passed
score: 18/18 must-haves verified
---

# Phase 05 Verification Report: On-Demand Incident Reports and PDF

## Executive Summary

Phase 05 đã hoàn thành toàn diện tất cả các mục tiêu, tiêu chí thành công và yêu cầu kỹ thuật được đặt ra trong lộ trình (`REP-01`, `REP-02`, `REP-03`, `REP-04`, `REP-05`, `REP-06` và tiêu chuẩn nghiệm thu `EVAL-03`). Toàn bộ 4 kế hoạch (`05-01` đến `05-04`) đã được triển khai, kiểm thử độc lập và kiểm chứng tích hợp end-to-end với 209/209 bài kiểm thử backend thành công và bản dựng frontend Next.js Turbopack hoàn tất không lỗi.

- **Phase Status:** passed
- **Score:** 18/18 must-haves verified (100%)
- **Requirements Verified:** REP-01, REP-02, REP-03, REP-04, REP-05, REP-06, EVAL-03
- **Regression Suite:** 209/209 tests passed, 0 failures

---

## Detailed Must-Haves Verification

### Plan 05-01: Report Data Contracts & Deterministic Metrics Aggregator

| # | Must-Have Statement | Status | Code Evidence |
|---|---------------------|--------|---------------|
| 1 | Chuyển đổi múi giờ chuẩn xác từ `Asia/Ho_Chi_Minh` (UTC+7) sang UTC cho các kỳ Ngày, Tuần, Tháng, và Khoảng tùy chọn với biên thời gian cố định (00:00:00.000000 đến 23:59:59.999999). | VERIFIED | `backend/app/modules/reports/aggregator.py`: `compute_period_bounds()` hỗ trợ đầy đủ `PeriodTypeEnum.DAILY`, `WEEKLY`, `MONTHLY`, `CUSTOM` kèm unit tests trong `backend/tests/unit/test_report_service.py`. |
| 2 | Phân tách độc lập tổng số ticket và số sự cố (incident); số liệu được tính 100% tất định từ canonical records và incident analyses, tuyệt đối không lấy từ context top-k của LLM. | VERIFIED | `backend/app/modules/reports/aggregator.py`: `aggregate_report_metrics()` đếm độc lập `total_incidents = len(incident_analyses)` và `total_tickets = sum(1 for r in canonical_records if r.profile_id == 'ticket')`. |
| 3 | Phân tích chi tiết (breakdown) theo Hệ thống (WMS, TMS, ERP, API), Nhóm lỗi (Database, Network, Timeout, Auth), và Mức độ ưu tiên (P1, P2, P3, P4) được tổng hợp tất định. | VERIFIED | `backend/app/modules/reports/aggregator.py`: `systems_map`, `error_groups_map`, `priorities_map` lặp qua toàn bộ bản ghi thực tế trong kỳ và tính toán chính xác số lượng. |
| 4 | MTTR (Mean Time to Resolve) được tính toán nghiêm ngặt chỉ trên các sự cố đã hoàn tất (`resolved`/`closed`); các sự cố chưa giải quyết được tách biệt là "Đang mở" và không làm sai lệch MTTR. | VERIFIED | `backend/app/modules/reports/aggregator.py`: `resolved_incidents` được lọc theo trạng thái đóng, tính `duration_minutes = (resolved_at - created_at)`. Sự cố mở được lưu trong `open_incidents`. |
| 5 | Quy tắc nhóm lỗi lặp lại (Recurring Errors): Tự động phát hiện các cặp `[Hệ thống + Nhóm lỗi]` xuất hiện $\ge 2$ lần, liệt kê số lần lặp và danh sách các mã vận đơn (`affected_orders`) bị ảnh hưởng. | VERIFIED | `backend/app/modules/reports/aggregator.py`: gom nhóm theo `(system, error_group)` và lọc `count >= 2`, trích xuất `order_id` từ `classification_json` hoặc canonical metadata. |

### Plan 05-02: WeasyPrint 70.0 PDF Generator & Jinja2 Template

| # | Must-Have Statement | Status | Code Evidence |
|---|---------------------|--------|---------------|
| 6 | Tích hợp WeasyPrint 70.0 và cài đặt đầy đủ các thư viện native hệ điều hành (`libpango-1.0-0`, `libcairo2`, `fonts-liberation`, `fonts-dejavu-core`) trong Dockerfile. | VERIFIED | `backend/Dockerfile`, `backend/pyproject.toml`: cài đặt `weasyprint==70.0` và native packages, đảm bảo hỗ trợ đầy đủ phông chữ tiếng Việt có dấu. |
| 7 | Mẫu in Jinja2 chuẩn A4 (`incident_report.html`) áp dụng CSS Paged Media `@page` với đánh số trang tự động `Trang counter(page) / counter(pages)` và lặp lại tiêu đề bảng khi ngắt trang (`thead { display: table-header-group; }`). | VERIFIED | `backend/app/modules/reports/templates/incident_report.html`: CSS `@page` định nghĩa `@bottom-right { content: "Trang " counter(page) " / " counter(pages); }` và `thead { display: table-header-group; }`. |
| 8 | Cơ chế bảo vệ SSRF tuyệt đối: Chặn toàn bộ network requests ra ngoài khi sinh PDF thông qua `_blocked_url_fetcher`, bật `autoescape=True` trong Jinja2 ngăn chặn HTML/XSS injection. | VERIFIED | `backend/app/modules/reports/pdf_generator.py`: hàm `_blocked_url_fetcher` ném `PermissionError` đối với mọi URL bên ngoài; `jinja2.Environment(autoescape=True)`. |
| 9 | Xuất tệp PDF hợp lệ với tiêu đề nhị phân chuẩn `%PDF-1.` và hiển thị đúng tiếng Việt có dấu. | VERIFIED | `backend/tests/unit/test_pdf_generator.py`: kiểm thử sinh PDF trả về bytes bắt đầu bằng `b"%PDF-1."` và xác thực chuỗi tiếng Việt phức tạp không gây lỗi glyph. |

### Plan 05-03: Reports Persistence, API Routes & Live Scope Recheck

| # | Must-Have Statement | Status | Code Evidence |
|---|---------------------|--------|---------------|
| 10 | Mô hình dữ liệu SQLAlchemy `Report` và migration Alembic `0005_incident_reports` với các cột JSONB lưu trữ metrics, narrative và provenance metadata. | VERIFIED | `backend/app/database/models.py`, `backend/alembic/versions/0005_incident_reports.py`: bảng `reports` có index trên `created_at` và `account_id`. |
| 11 | `ReportNarrativeSynthesizer` sinh nhận định tóm tắt và khuyến nghị SOP có che giấu secret (`mask_secrets`) trước khi gửi egress sang LLM; cơ chế fallback tất định (SYS-05) khi không có LLM. | VERIFIED | `backend/app/modules/reports/narrative.py`: che tokens/passwords bằng regex `mask_secrets` và cung cấp `_build_deterministic_fallback` bảo đảm không làm gián đoạn báo cáo. |
| 12 | `ReportService` chụp ảnh tức thời (snapshot provenance) lưu nguồn gốc dữ liệu: `source_id`, `version_number`, `logical_filename`, `dataset_id`. | VERIFIED | `backend/app/modules/reports/service.py`: `generate_report()` truy vấn `SourceVersion` và `Source` để lưu snapshot vào `provenance_json`. |
| 13 | Thực thi Live Scope Recheck (AUTH-04, REP-06): Kiểm tra quyền hiện tại của người dùng đối với các dataset trong báo cáo tại thời điểm xem chi tiết hoặc tải PDF; từ chối HTTP 403 Forbidden nếu quyền đã bị thu hồi. | VERIFIED | `backend/app/modules/reports/service.py`: `get_report()` kiểm tra `did not in allowed_dataset_ids` và raise `HTTPException(403)`. Kiểm chứng qua `test_report_scope_recheck.py`. |
| 14 | Các endpoint REST API `/api/v1/reports`: Tạo báo cáo (`POST /generate`), danh sách (`GET /`), chi tiết (`GET /{id}`), và tải PDF (`GET /{id}/pdf`). | VERIFIED | `backend/app/api/reports.py`: phân quyền RBAC (`report.create`, `report.view`), kiểm tra CSRF token và trả về `StreamingResponse` cho file PDF. |

### Plan 05-04: Next.js Reports Workspace UI & EVAL-03 Acceptance

| # | Must-Have Statement | Status | Code Evidence |
|---|---------------------|--------|---------------|
| 15 | Không gian làm việc Next.js Reports (`/reports`) với 2 tab chuyển đổi: Tạo báo cáo mới và Lịch sử báo cáo đã lập. | VERIFIED | `frontend/src/app/(workspace)/reports/page.tsx`: tab bar chuyển đổi mượt mà, hỗ trợ cả vai trò Admin và Kỹ thuật viên. |
| 16 | Giao diện hiển thị đầy đủ thẻ KPI tổng quan, bảng phân tích theo Hệ thống / Nhóm lỗi / Mức ưu tiên, danh sách lỗi lặp lại kèm badge mã đơn, tóm tắt điều hành và khuyến nghị SOP từ AI. | VERIFIED | `frontend/src/app/(workspace)/reports/page.tsx`: tích hợp các card KPI (Tổng sự cố, Ticket IT, MTTR, Tỷ lệ hoàn tất), bảng phân tích và badge đơn hàng màu vàng/đỏ. |
| 17 | Modal xem chi tiết nguồn trích dẫn (Provenance Metadata) và nút tải PDF tiếng Việt với xử lý thông báo lỗi HTTP 403 khi quyền dataset bị thu hồi. | VERIFIED | `frontend/src/app/(workspace)/reports/page.tsx`: modal Provenance hiển thị danh sách tệp/phiên bản nguồn; hàm `handleDownloadPdf` bắt mã 403 và thông báo rõ ràng cho kỹ thuật viên. |
| 18 | Bộ kiểm thử nghiệm thu EVAL-03 xác thực số liệu ground truth khớp dữ liệu mẫu và kiểm chứng từ chối tải PDF khi mất quyền dataset. | VERIFIED | `backend/tests/integration/test_reports_e2e_acceptance.py`: 7/7 kịch bản nghiệm thu kiểm tra độc lập ticket/incident, MTTR chỉ tính cho đơn đóng, và kiểm tra thu hồi quyền trả về HTTP 403. |

---

## Traceability Matrix (REQUIREMENTS.md)

| Requirement | Description | Status | Evidence |
|-------------|-------------|--------|----------|
| **REP-01** | Tạo báo cáo theo ngày/tuần/tháng/tùy chọn trong scope dataset, timezone Asia/Ho_Chi_Minh. | **Validated** | `compute_period_bounds()` trong `aggregator.py`, `ReportFilterDTO`, API `POST /api/v1/reports/generate`. |
| **REP-02** | Đếm riêng ticket và incident; số liệu hệ thống/lỗi/ưu tiên tính tất định 100% từ canonical records. | **Validated** | `aggregate_report_metrics()` trong `aggregator.py`, `test_reports_e2e_acceptance.py`. |
| **REP-03** | MTTR tính riêng cho sự cố đã đóng; sự cố đang mở hiển thị "Đang mở" và "Chưa hoàn tất", không suy đoán. | **Validated** | `aggregator.py`: `resolved_incidents` và `open_incidents`, `test_mttr_calculation_strict_to_closed_only`. |
| **REP-04** | Lỗi lặp lại theo quy tắc grouping `[Hệ thống + Nhóm lỗi] >= 2`, đề xuất SOP và bằng chứng. | **Validated** | `aggregator.py`: `recurring_errors`, `narrative.py`: `ReportNarrativeSynthesizer`. |
| **REP-05** | Lưu snapshot provenance (nguồn, phiên bản, bộ lọc) và kiểm tra quyền khi mở lại. | **Validated** | `provenance_json` trong `Report` model, `service.py`: `ReportService.get_report()`. |
| **REP-06** | Xem trước Web, tải PDF tiếng Việt (WeasyPrint 70.0), Live Scope Recheck từ chối HTTP 403 nếu quyền bị thu hồi. | **Validated** | `pdf_generator.py`, `incident_report.html`, `test_report_scope_recheck.py`, Next.js Reports Workspace UI. |
| **EVAL-03** | Nghiệm thu ground truth metrics/PDF, timezone biên kỳ và từ chối truy cập khi thu hồi quyền. | **Validated** | `backend/tests/integration/test_reports_e2e_acceptance.py` pass 100%. |

---

## Automated Test Results

### 1. Backend Test Suite (Pytest)
```
Platform: Linux (Docker Container)
Total Tests: 209
Passed: 209
Failed: 0
Duration: 75.38s
```
Tất cả các module unit tests, integration tests và E2E tests (auth, datasets, sources, pgvector, log analysis, incidents, reports, e2e acceptance) đều đạt trạng thái PASSED.

### 2. Frontend Build (Next.js Turbopack)
```
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

Result: Compiled successfully in 411ms. TypeScript validation passed in 1936ms. 10 static pages prerendered. 0 errors.
```

---

## Conclusion

Phase 05 đạt trạng thái **passed**, hoàn thành toàn bộ 18/18 tiêu chí mục tiêu và đáp ứng 100% các yêu cầu kỹ thuật và ràng buộc kiến trúc. Dự án sẵn sàng để đánh dấu hoàn tất Phase 05 và chuyển giao sang Phase 06 (hoặc kiểm toán milestone).

## Verification Complete.

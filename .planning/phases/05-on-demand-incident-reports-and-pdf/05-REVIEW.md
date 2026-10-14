---
status: clean
phase: "05"
files_reviewed: 15
findings:
  critical: 0
  warning: 0
  info: 0
  total: 0
---

# Phase 05 Code Review Report: On-Demand Incident Reports and PDF

## Executive Summary

Toàn bộ 15 tệp mã nguồn và kiểm thử thuộc Phase 05 (backend contracts, deterministic aggregator, PDF generator engine, Jinja2 template, LLM narrative synthesizer với secret masking, SQLAlchemy model, Alembic migration, FastAPI routes, frontend workspace component, và bộ test suite unit/integration/E2E) đã được rà soát kỹ lưỡng theo các tiêu chuẩn bảo mật, tính toàn vẹn dữ liệu, ranh giới quyền truy cập và kiến trúc hệ thống.

- **Status:** clean
- **Files Reviewed:** 15
- **Findings:**
  - Critical: 0
  - Warning: 0
  - Info: 0
  - Total: 0

---

## Phạm vi rà soát (File Scope)

### Backend Reports Core & Aggregation
1. `backend/app/modules/reports/contracts.py`: Hợp đồng dữ liệu Pydantic V2 (`PeriodTypeEnum`, `ReportFilterDTO`, `SystemBreakdownDTO`, `ErrorGroupBreakdownDTO`, `PriorityBreakdownDTO`, `RecurringErrorDTO`, `ReportMetricsDTO`, `ReportNarrativeDTO`, `ReportDetailDTO`). Kiểm tra `frozen=False`, validation đầy đủ cho các kiểu khoảng thời gian ngày/tuần/tháng/tùy chọn.
2. `backend/app/modules/reports/aggregator.py`: Hàm `compute_period_bounds` chuyển đổi chuẩn múi giờ `Asia/Ho_Chi_Minh` (UTC+7) sang UTC mốc thời gian bắt đầu (00:00:00.000000) và kết thúc (23:59:59.999999). Hàm `aggregate_report_metrics` tính toán 100% tất định số liệu từ bản ghi canonical và phân tích sự cố: phân tách độc lập incident và ticket count; MTTR chỉ tính toán trên các sự cố đã đóng (`resolved`/`closed`); sự cố mở được phân loại riêng; phân nhóm lỗi lặp lại theo quy tắc `[Hệ thống + Nhóm lỗi]` xuất hiện $\ge 2$ lần kèm danh sách mã vận đơn liên quan.
3. `backend/app/modules/reports/pdf_generator.py`: Bộ sinh PDF sử dụng WeasyPrint 70.0. Tích hợp cơ chế bảo vệ SSRF tuyệt đối với `_blocked_url_fetcher` ngăn chặn mọi outbound network request; bật `autoescape=True` trong Jinja2 tránh XSS/HTML injection; định dạng ngày giờ hiển thị theo múi giờ Việt Nam.
4. `backend/app/modules/reports/templates/incident_report.html`: Mẫu báo cáo A4 chuyên nghiệp tuân thủ chuẩn in ấn CSS Paged Media `@page`, lặp lại tiêu đề bảng khi sang trang (`thead { display: table-header-group; }`), đánh số trang `Trang counter(page) / counter(pages)`, bố cục phân tách rõ ràng giữa số liệu tất định và tổng hợp định tính LLM.
5. `backend/app/modules/reports/narrative.py`: `ReportNarrativeSynthesizer` sinh tóm tắt vận hành và khuyến nghị SOP từ số liệu đã tính sẵn. Áp dụng `mask_secrets` che giấu JWT token, khóa API, mật khẩu, authorization headers trước khi gửi ngữ cảnh sang LLM; cơ chế fallback tất định (SYS-05) khi không có LLM Provider hoặc khi gọi API gặp lỗi.

### Backend Data, Persistence & API Routes
6. `backend/app/modules/reports/service.py`: `ReportService` điều phối tạo báo cáo, kiểm tra quyền dataset ban đầu, chụp snapshot nguồn gốc (provenance metadata: source ID, version number, filename, dataset ID), lưu trữ bảng `reports`, và thực thi kiểm tra IDOR (Admin hoặc chính chủ). Đặc biệt áp dụng Live Scope Recheck (AUTH-04, REP-06) khi xem chi tiết hoặc tải xuống PDF: nếu bất kỳ dataset nào trong báo cáo bị thu hồi sau thời điểm tạo, API lập tức trả về HTTP 403 Forbidden.
7. `backend/app/database/models.py`: Thực thể `Report` với khóa ngoại `account_id`, các trường mốc thời gian UTC, và các cột `JSONB` lưu trữ `dataset_ids`, `metrics_json`, `narrative_json`, `provenance_json`.
8. `backend/alembic/versions/0005_incident_reports.py`: Migration Alembic khởi tạo bảng `reports` cùng các chỉ mục tối ưu hóa truy vấn (`ix_reports_account_id`, `ix_reports_created_at`).
9. `backend/app/api/reports.py`: Router FastAPI `/api/v1/reports` cung cấp các endpoints: `POST /generate`, `GET /`, `GET /{id}`, `GET /{id}/pdf`. Tích hợp đầy đủ RBAC, CSRF token verification và response streaming dạng `application/pdf`.
10. `backend/app/api/health.py`: Bổ sung mã migration `0005_incident_reports` vào whitelist kiểm tra độ sẵn sàng database readiness probe.
11. `backend/app/main.py`: Đăng ký router reports vào ứng dụng FastAPI chính.

### Frontend UI & Contracts
12. `frontend/src/lib/contracts.ts`: Cập nhật các interface TypeScript tương ứng đầy đủ với contracts backend: `ReportFilter`, `SystemBreakdown`, `ErrorGroupBreakdown`, `PriorityBreakdown`, `RecurringError`, `ReportMetrics`, `ReportNarrative`, `ReportDetail`, `ReportSummaryItem`.
13. `frontend/src/components/Sidebar.tsx`: Bổ sung mục điều hướng "Báo cáo sự cố" (`/reports`) cho vai trò Quản trị viên (`admin`) và Kỹ thuật viên (`technician`).
14. `frontend/src/app/(workspace)/reports/page.tsx`: Giao diện không gian làm việc báo cáo hoàn chỉnh với 2 tab: Tạo báo cáo (bộ lọc kỳ ngày/tuần/tháng/tùy chọn, chọn dataset, thẻ KPI tổng quan, bảng phân tích theo hệ thống/nhóm lỗi/độ ưu tiên, danh sách lỗi lặp lại kèm badge mã đơn, phân tích định tính LLM, modal xem chi tiết nguồn trích dẫn provenance, nút tải PDF có xử lý lỗi 403 Live Scope Recheck) và Lịch sử báo cáo (danh sách báo cáo đã lập, nút xem lại và tải PDF trực tiếp).

### Verification & Testing
15. Bộ kiểm thử toàn diện:
  - Unit tests: `backend/tests/unit/test_report_service.py` (7 tests tính toán tất định, biên múi giờ, phân nhóm lỗi lặp lại), `backend/tests/unit/test_pdf_generator.py` (3 tests sinh PDF WeasyPrint, phông chữ tiếng Việt, kiểm tra magic bytes `%PDF-1.`).
  - Integration tests: `backend/tests/integration/test_reports_api.py` (tạo và truy vấn báo cáo qua REST API), `backend/tests/integration/test_report_scope_recheck.py` (kiểm tra từ chối HTTP 403 khi quyền dataset bị thu hồi).
  - E2E Acceptance test: `backend/tests/integration/test_reports_e2e_acceptance.py` (kiểm chứng tiêu chuẩn nghiệm thu EVAL-03, đối chiếu số liệu ground truth độc lập giữa ticket và incident, MTTR chỉ tính cho đơn đã đóng, và chặn tải PDF khi mất quyền dataset).

---

## Đánh giá chi tiết (Detailed Findings)

- **Bảo mật (Security):**
  - **SSRF:** Bộ sinh PDF chặn hoàn toàn yêu cầu mạng ra ngoài qua `_blocked_url_fetcher`. Mọi tài nguyên HTML/CSS đều nội bộ.
  - **Data Leakage:** Ngữ cảnh gửi đến LLM được bóc tách và che giấu secret (`mask_secrets`), chỉ gửi các trường tóm tắt cần thiết, không gửi file nguyên bản.
  - **Live Scope Recheck (AUTH-04, REP-06):** Ngăn chặn hoàn toàn việc rò rỉ dữ liệu lịch sử khi kỹ thuật viên bị điều chỉnh phân quyền dataset.
- **Tính toán số liệu tất định (Deterministic Metrics):**
  - Số liệu tổng hợp được tính toán 100% bằng code logic từ database canonical records, tuyệt đối không phụ thuộc vào context top-k hay hallucination của LLM.
- **Tính toàn vẹn giao diện và bản in (Rendering & Typography):**
  - Báo cáo HTML và PDF hiển thị chuẩn xác tiếng Việt có dấu nhờ bộ phông chữ Liberation và DejaVu đã đóng gói trong container Docker.

---

## Kết luận

Phase 05 đạt trạng thái **clean**, tuân thủ nghiêm ngặt toàn bộ các ràng buộc kiến trúc, kiểm tra bảo mật và tiêu chuẩn nghiệm thu đề ra. Không phát hiện lỗi nghiêm trọng hay cảnh báo cần khắc phục thêm.

---
phase: 05-on-demand-incident-reports-and-pdf
plan: "03"
subsystem: report-persistence-api-and-scope-recheck
tags: [reports-persistence, alembic, fastapi, live-scope-recheck, idor, streaming-response, integration-tests]
requires: [05-02]
provides:
  - Database model Report and Alembic migration 0005_incident_reports in backend/app/database/models.py and backend/alembic/versions/0005_incident_reports.py
  - Whitelist integration in backend/app/api/health.py and tests in test_migrations.py
  - ReportNarrativeSynthesizer with secret masking and SYS-05 deterministic fallback in backend/app/modules/reports/narrative.py
  - ReportService complete coordinator with persistence, IDOR verification, and Live Scope Recheck in backend/app/modules/reports/service.py
  - FastAPI reports router registered at /api/v1/reports with endpoints /generate, /history, /{id}, /{id}/pdf, /{id}/provenance
  - Integration test suites covering endpoints, IDOR prevention, and live scope permission revocation in backend/tests/integration/test_reports_api.py and test_report_scope_recheck.py
affects: [05-04]
tech-stack:
  added: []
  patterns: [live-scope-recheck, idor-protection, streaming-response, deterministic-fallback-narrative, alembic-version-whitelist]
key-files:
  created:
    - backend/alembic/versions/0005_incident_reports.py
    - backend/app/modules/reports/narrative.py
    - backend/app/api/reports.py
    - backend/tests/integration/test_reports_api.py
    - backend/tests/integration/test_report_scope_recheck.py
  modified:
    - backend/app/database/models.py
    - backend/app/api/health.py
    - backend/app/main.py
    - backend/app/modules/reports/service.py
    - backend/tests/conftest.py
    - backend/tests/integration/test_migrations.py
key-decisions:
  - "Lưu trữ báo cáo trong bảng reports với snapshot số liệu metrics_json, danh sách dataset_ids, narrative_json và provenance_json (D-04, D-05)."
  - "Bổ sung revision '0005_incident_reports' vào danh sách database_ready() trong health.py và test_migrations.py để đảm bảo Docker healthcheck luôn đạt trạng thái healthy."
  - "Bảo vệ IDOR: Admin được xem tất cả báo cáo; Kỹ thuật viên chỉ được xem và tải các báo cáo do chính mình tạo (T-05-05)."
  - "Thực thi Live Scope Recheck (AUTH-04, REP-06): Đối chiếu trực tiếp quyền dataset hiện hành của tài khoản khi xem báo cáo hoặc tải PDF. Nếu có bất kỳ dataset nguồn nào bị thu hồi quyền, backend từ chối ngay lập tức với HTTP 403 Forbidden (T-05-06)."
  - "Tích hợp SYS-05 fallback: Nếu LLM Provider gặp sự cố hoặc timeout, hệ thống tự động sinh nhận định dựa trên số liệu KPI có sẵn và gắn cờ cảnh báo rõ ràng mà không làm gián đoạn việc tạo báo cáo."
requirements-completed: [REP-05, REP-06, AUTH-04, SYS-05]
actuals:
  tokens: 36000
  tasks: 3
  commits: 1
duration: 15min
completed: 2026-10-14
status: complete
---

# Phase 5 Plan 03: Report Persistence, Database Migration & FastAPI API Routes Summary

**Triển khai toàn diện lớp lưu trữ báo cáo (bảng `reports`, migration `0005_incident_reports`), bộ tổng hợp nhận định LLM bảo mật kèm fallback tất định SYS-05, hệ thống API router `/api/v1/reports` với cơ chế bảo vệ IDOR và Live Scope Recheck nghiêm ngặt theo REP-05, REP-06, AUTH-04, SYS-05.**

## Hoàn thành các nhiệm vụ

### 1. Schema Migration & Persistence for Reports Table (Task 05-03-01)
- Cập nhật `backend/app/database/models.py`: Thêm entity `Report` với các trường `id`, `account_id`, `title`, `period_type`, `start_time`, `end_time`, `dataset_ids`, `metrics_json`, `narrative_json`, `provenance_json` và `created_at`.
- Tạo migration Alembic `0005_incident_reports.py` với chỉ mục `ix_reports_account_id` và `ix_reports_created_at`.
- Cập nhật whitelist migration trong `backend/app/api/health.py` và `test_migrations.py`, chạy migration thành công lên head, xác nhận `/health/ready` trả về 200 OK.

### 2. Guarded Narrative Synthesizer & Report Service Layer (Task 05-03-02)
- Triển khai `ReportNarrativeSynthesizer` trong `backend/app/modules/reports/narrative.py`:
  - Thực thi `mask_secrets` trên prompt trước khi gửi đến LLM Provider (SYS-03).
  - Tích hợp bộ quy tắc sinh nhận định dự phòng `_build_deterministic_fallback` xử lý ngoại lệ khi LLM timeout hoặc lỗi (SYS-05).
- Triển khai toàn diện `ReportService` trong `backend/app/modules/reports/service.py`:
  - `generate_report`: Xác thực quyền truy cập dataset, tính toán mốc biên UTC+7 -> UTC, truy vấn dữ liệu nguồn, tính toán số liệu tất định 100%, thu thập provenance snapshot và lưu vào DB.
  - `get_report_detail`: Kiểm tra phân quyền IDOR và thực thi Live Scope Recheck (từ chối 403 nếu quyền dataset bị thu hồi).
  - `get_report_pdf`: Thực thi Live Scope Recheck và biên dịch PDF bytes qua WeasyPrint.
  - `list_reports`: Liệt kê lịch sử báo cáo với bộ lọc loại bỏ các báo cáo thuộc dataset đã bị thu hồi quyền.

### 3. FastAPI Report Router & Integration Test Suite (Task 05-03-03)
- Tạo `backend/app/api/reports.py` và đăng ký vào `backend/app/main.py`:
  - `POST /api/v1/reports/generate`: Tạo báo cáo theo kỳ.
  - `GET /api/v1/reports/history`: Xem lịch sử tạo báo cáo.
  - `GET /api/v1/reports/{report_id}`: Xem chi tiết báo cáo.
  - `GET /api/v1/reports/{report_id}/pdf`: Tải file PDF qua `StreamingResponse`.
  - `GET /api/v1/reports/{report_id}/provenance`: Xem nguồn tham chiếu.
- Tạo 2 bộ kiểm thử tích hợp:
  - `backend/tests/integration/test_reports_api.py`: 4 bài test xác thực tạo báo cáo, kiểm soát IDOR giữa 2 kỹ thuật viên, tải PDF và xem provenance.
  - `backend/tests/integration/test_report_scope_recheck.py`: Xác thực ca kiểm thử cốt lõi Live Scope Recheck (AUTH-04, REP-06) — khi Admin thu hồi quyền dataset, mọi yêu cầu xem chi tiết hoặc tải PDF lập tức nhận HTTP 403 Forbidden.
- Toàn bộ 10/10 tests tích hợp chạy qua `backend-test` trên database cách ly đều đạt 100% passed.

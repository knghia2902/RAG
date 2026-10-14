---
phase: 04-logistics-incident-and-ticket-analysis
plan: "04"
subsystem: incident-service-persistence-and-api
tags: [incident-service, postgresql, alembic, fastapi, idor-protection, live-scope-recheck, integration-tests]
requires: [04-03]
provides:
  - IncidentAnalysis database model in backend/app/database/models.py
  - Database schema migration 0004_incident_analysis.py creating incident_analyses table
  - IncidentAnalysisService coordinating log correlation, vector SOP matching, reasoning, and persistence in backend/app/modules/log_analysis/service.py
  - FastAPI router (/api/v1/incidents) with POST /analyze, POST /upload-ticket, GET /history, GET /{analysis_id}, and GET /citations/{citation_id}/preview
  - Integration tests for incident API routes and real-time Live Scope Recheck revocation enforcement
affects: [04-05]
tech-stack:
  added: []
  patterns: [database-persistence-jsonb, idor-authorization-check, live-scope-recheck-403, multipart-file-intake]
key-files:
  created:
    - backend/alembic/versions/0004_incident_analysis.py
    - backend/app/modules/log_analysis/service.py
    - backend/app/api/incidents.py
    - backend/tests/integration/test_incident_api.py
    - backend/tests/integration/test_incident_scope_recheck.py
  modified:
    - backend/app/database/models.py
    - backend/app/api/schemas.py
    - backend/app/main.py
    - backend/app/modules/log_analysis/correlator.py
    - backend/app/modules/log_analysis/sop_matcher.py
    - backend/app/modules/tickets/service.py
    - backend/tests/conftest.py
key-decisions:
  - "Lưu trữ toàn bộ kết quả phân tích sự cố (classification, timeline, hypotheses, recommended_actions, citations) dưới dạng JSONB trong bảng incident_analyses để phục vụ tra cứu lịch sử và báo cáo ở Phase 5."
  - "Áp dụng cơ chế Live Scope Recheck (D-05, AUTH-04) thời gian thực trên cả hai endpoint xem chi tiết sự cố và click mở trích dẫn: nếu quyền truy cập dataset bị thu hồi, hệ thống ngay lập tức trả về HTTP 403 Forbidden."
  - "Phòng chống IDOR (T-04-07): Kỹ thuật viên chỉ có thể xem các bản ghi phân tích do chính mình tạo (hoặc quản trị viên xem toàn bộ)."
  - "Hỗ trợ tiếp nhận tệp ticket đa định dạng (.json, .csv) qua multipart upload, tự động phân tích ca sự cố đầu tiên trong lô và phản hồi lỗi 422 chi tiết theo từng dòng."
requirements-completed: [INC-01, INC-02]
actuals:
  tokens: 46000
  tasks: 3
  commits: 1
duration: 15min
completed: 2026-10-14
status: complete
---

# Phase 4 Plan 04: Incident Service, Migration & API Routes Summary

**Thiết lập hạ tầng lưu trữ cơ sở dữ liệu (`incident_analyses`), hoàn thiện Service layer tích hợp và cung cấp các endpoint API FastAPI tại `/api/v1/incidents` cho việc phân tích sự cố, tải tệp ticket, xem lịch sử, và thực thi kiểm tra quyền thời gian thực (Live Scope Recheck) theo yêu cầu INC-01, INC-02 và AUTH-04.**

## Hoàn thành các nhiệm vụ

### 1. Schema Migration for Incident Analysis Persistence (Task 04-04-01)
- Thêm mô hình ORM `IncidentAnalysis` vào `backend/app/database/models.py` gồm các trường `account_id`, `order_id`, `ticket_id`, `input_mode`, `title`, và các trường dữ liệu `JSONB` (`classification_json`, `timeline_json`, `analysis_json`, `citations_json`).
- Tạo và thực thi migration Alembic `backend/alembic/versions/0004_incident_analysis.py` (down_revision = `0003_pgvector_and_chat`), tạo bảng `incident_analyses` và các chỉ mục tương ứng trên PostgreSQL.

### 2. Incident Analysis Service & FastAPI Router (Task 04-04-02)
- Triển khai `IncidentAnalysisService` trong `backend/app/modules/log_analysis/service.py`:
  - Rà soát quyền dataset của tài khoản bằng `allowed_dataset_ids`.
  - Truy vấn các bản ghi `CanonicalRecord` chứa `order_id` trong phạm vi được cấp quyền.
  - Phối hợp `CrossSystemLogCorrelator`, `SOPMatcher` và `IncidentReasoner`.
  - Lưu trữ kết quả phân tích vào bảng `incident_analyses`.
- Tạo router `backend/app/api/incidents.py` với 5 endpoint:
  - `POST /analyze`: Phân tích sự cố theo Order ID (Quick Form).
  - `POST /upload-ticket`: Upload tệp ticket (.json / .csv), thẩm định schema nghiêm ngặt và kích hoạt phân tích.
  - `GET /history`: Liệt kê lịch sử phân tích sự cố của người dùng (hoặc toàn hệ thống đối với Admin).
  - `GET /{analysis_id}`: Xem chi tiết ca phân tích kèm Live Scope Recheck.
  - `GET /citations/{citation_id}/preview`: Xem trước đoạn trích log gốc kèm kiểm tra quyền Live Scope Recheck.
- Đăng ký `incidents.router` trong `backend/app/main.py`.

### 3. Incident API Integration Tests & Live Scope Recheck (Task 04-04-03)
- Viết `backend/tests/integration/test_incident_api.py` kiểm thử toàn diện:
  - `test_analyze_order_endpoint`: Xác thực phản hồi 200 OK với đủ 4 khối kết quả chuẩn.
  - `test_upload_valid_ticket_json_and_csv`: Xác thực upload tệp JSON và CSV hợp lệ.
  - `test_upload_invalid_ticket_schema_422`: Xác thực chặn file sai schema với mã 422 và danh sách lỗi dòng.
  - `test_incident_history`: Xác thực tra cứu danh sách lịch sử phân tích.
- Viết `backend/tests/integration/test_incident_scope_recheck.py`:
  - `test_live_scope_recheck_revocation_denied`: Xác thực cơ chế Live Scope Recheck; khi admin thu hồi quyền dataset, mọi yêu cầu xem chi tiết sự cố hoặc mở xem trích dẫn lập tức bị chặn với 403 Forbidden.
- Toàn bộ 5/5 integration tests đều đạt 100% PASSED trên môi trường cơ sở dữ liệu test cách ly.

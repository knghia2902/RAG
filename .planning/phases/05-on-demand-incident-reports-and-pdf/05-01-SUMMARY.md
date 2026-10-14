---
phase: 05-on-demand-incident-reports-and-pdf
plan: "01"
subsystem: report-contracts-and-metrics-aggregator
tags: [reports, pydantic, deterministic-metrics, timezone, mttr, recurring-errors, unit-tests]
requires: []
provides:
  - Pydantic V2 Report contracts (PeriodTypeEnum, ReportFilterDTO, ReportMetricsDTO, ReportDetailDTO) in backend/app/modules/reports/contracts.py
  - Timezone-aware bounds computation in Asia/Ho_Chi_Minh (UTC+7) converted to UTC in backend/app/modules/reports/aggregator.py
  - 100% deterministic metric aggregation engine for tickets, incidents, MTTR, breakdowns, and recurring errors in backend/app/modules/reports/aggregator.py
  - ReportService base coordinator in backend/app/modules/reports/service.py
  - Comprehensive unit test suite with 7 test cases in backend/tests/unit/test_report_service.py
affects: [05-02, 05-03, 05-04]
tech-stack:
  added: []
  patterns: [deterministic-aggregation, timezone-normalization, pydantic-v2, asvs-input-validation]
key-files:
  created:
    - backend/app/modules/reports/contracts.py
    - backend/app/modules/reports/aggregator.py
    - backend/app/modules/reports/service.py
    - backend/tests/unit/test_report_service.py
  modified: []
key-decisions:
  - "Áp dụng múi giờ chuẩn Asia/Ho_Chi_Minh (UTC+7) cho toàn bộ mốc biên báo cáo (00:00:00 đến 23:59:59.999999), chuẩn hóa về UTC khi truy vấn database."
  - "Số liệu ticket, incident, nhóm lỗi, hệ thống và mức ưu tiên tính tất định 100% từ canonical records và incident analyses, tuyệt đối không lấy từ top-k retrieval context."
  - "MTTR chỉ tính trên các sự cố/ticket đã hoàn tất (status RESOLVED/SUCCESS/CLOSED); các sự cố chưa đóng hiển thị 'Đang mở' và thời lượng là 'Chưa hoàn tất' (REP-03)."
  - "Lỗi lặp lại được gom nhóm theo cặp [Hệ thống + Mã lỗi/Nhóm lỗi] xuất hiện từ 2 lần trở lên (>= 2) trong kỳ (REP-04)."
requirements-completed: [REP-01, REP-02, REP-03, REP-04]
actuals:
  tokens: 28000
  tasks: 3
  commits: 1
duration: 8min
completed: 2026-10-14
status: complete
---

# Phase 5 Plan 01: Report Contracts & Deterministic Metrics Aggregation Engine Summary

**Xây dựng nền tảng DTOs và bộ tổng hợp số liệu báo cáo tất định 100% (`backend/app/modules/reports`), đảm bảo chuẩn hóa mốc thời gian UTC+7 sang UTC, tính toán độc lập số lượng ticket và incident, tính MTTR nghiêm ngặt cho các sự cố đã đóng và gom nhóm lỗi lặp lại theo REP-01, REP-02, REP-03, REP-04.**

## Hoàn thành các nhiệm vụ

### 1. Report Contracts & DTOs Definition (Task 05-01-01)
- Tạo `backend/app/modules/reports/contracts.py` với `PeriodTypeEnum` (`daily`, `weekly`, `monthly`, `custom`).
- Định nghĩa `ReportFilterDTO` có validator kiểm tra ngày bắt đầu không sau ngày kết thúc và giới hạn khoảng thời gian $\le 366$ ngày (T-05-01).
- Định nghĩa `RecurringErrorItemDTO`, `SystemDistributionDTO`, `PriorityDistributionDTO`, `ReportMetricsDTO`, `ReportNarrativeDTO` và `ReportDetailDTO` với `extra="forbid"` và `frozen=True`.

### 2. Timezone Normalization & Deterministic Aggregation Engine (Task 05-01-02)
- Triển khai `compute_period_bounds` trong `backend/app/modules/reports/aggregator.py`: xác định chính xác từ `00:00:00` đến `23:59:59.999999` giờ Việt Nam (`Asia/Ho_Chi_Minh`) cho các kỳ Ngày, Tuần, Tháng, Tùy chọn và quy đổi về UTC (D-01).
- Triển khai `aggregate_report_metrics`: tính toán chính xác tổng incident, ticket, phân loại đã hoàn tất vs đang mở, MTTR trung bình, phân bổ hệ thống/ưu tiên và gom nhóm lỗi lặp $\ge 2$ lần (D-02, D-03).
- Tạo lớp điều phối `ReportService` trong `backend/app/modules/reports/service.py`.

### 3. Report Aggregator Unit Test Suite (Task 05-01-03)
- Tạo `backend/tests/unit/test_report_service.py` với 7 bài kiểm thử đơn vị:
  - `test_filter_dto_validation`: Kiểm tra validation ngày hợp lệ/bất hợp lệ và giới hạn 366 ngày.
  - `test_compute_period_bounds_daily`: Kiểm tra mốc biên DAILY đúng múi giờ UTC+7 và UTC.
  - `test_compute_period_bounds_weekly_and_monthly`: Kiểm tra mốc biên đầu/cuối tuần và đầu/cuối tháng.
  - `test_compute_period_bounds_custom`: Kiểm tra khoảng ngày tùy chọn.
  - `test_aggregate_deterministic_metrics`: Kiểm tra đếm số lượng sự cố, ticket và phân bổ hệ thống.
  - `test_mttr_calculation_only_for_resolved`: Xác thực sự cố chưa đóng không bị tính giả định vào MTTR (trả về None).
  - `test_recurring_error_grouping_rule`: Xác thực lỗi lặp $\ge 2$ lần theo cặp `[Hệ thống + Mã lỗi]`.
- 100% tests vượt qua trong môi trường container backend.

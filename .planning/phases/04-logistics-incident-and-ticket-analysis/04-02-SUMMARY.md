---
phase: 04-logistics-incident-and-ticket-analysis
plan: "02"
subsystem: cross-system-log-correlation
tags: [log-analysis, correlation, timeline, failure-point, disambiguation, regex, unit-tests]
requires: [04-01]
provides:
  - Pydantic V2 Log Analysis contracts (TimelineEventDTO, CorrelatedOrderLogs) in backend/app/modules/log_analysis/contracts.py
  - Cross-system log correlation engine with exact order ID regex and failure point isolation in backend/app/modules/log_analysis/correlator.py
  - Comprehensive unit test suite covering order ID disambiguation (DH001 vs DH010/DH0011), chronological timeline ordering, and failure point isolation
affects: [04-03, 04-04, 04-05]
tech-stack:
  added: []
  patterns: [exact-regex-word-boundaries, chronological-event-sorting, first-failure-point-isolation, pydantic-v2]
key-files:
  created:
    - backend/app/modules/log_analysis/contracts.py
    - backend/app/modules/log_analysis/correlator.py
    - backend/tests/unit/test_log_correlator.py
  modified: []
key-decisions:
  - "Áp dụng regex r'\\b' + re.escape(order_id) + r'\\b' để phân biệt tuyệt đối giữa DH001 và các chuỗi tương tự như DH010, DH0011 hoặc DH001_OLD."
  - "Sắp xếp toàn bộ sự kiện theo thứ tự thời gian tăng dần từ chuỗi ISO 8601 UTC chuẩn hóa."
  - "Chỉ đánh dấu cờ is_failure_point=True duy nhất tại điểm đứt gãy đầu tiên trong chuỗi sự kiện (mã HTTP >= 500, TIMEOUT hoặc ERROR) theo quyết định D-04."
  - "Tự động đánh số trích dẫn citation_id tuần tự từ 1 trên toàn bộ timeline đã chuẩn hóa."
requirements-completed: [INC-01]
actuals:
  tokens: 42000
  tasks: 3
  commits: 1
duration: 10min
completed: 2026-10-14
status: complete
---

# Phase 4 Plan 02: Cross-System Log Correlation Engine Summary

**Triển khai engine đối soát log đa hệ thống (`backend/app/modules/log_analysis/correlator.py`) có khả năng truy xuất toàn bộ log WMS, API Gateway và TMS theo mã đơn hàng (`order_id`), phân biệt tuyệt đối không lẫn mã tương tự (`DH001` vs `DH010`), chuẩn hóa timestamp và sắp xếp chuỗi sự kiện tuyến tính, tự động định vị điểm đứt gãy đồng bộ đầu tiên theo yêu cầu INC-01 và quyết định D-04.**

## Hoàn thành các nhiệm vụ

### 1. Log Analysis & Correlation Contracts (Task 04-02-01)
- Tạo `backend/app/modules/log_analysis/contracts.py` định nghĩa các model Pydantic v2:
  - `TimelineEventDTO`: gồm `event_id`, `timestamp`, `system` (`SystemEnum`), `event_name`, `status`, `is_failure_point`, `citation_id`, `source_filename`, `line_number`, `raw_snippet`.
  - `CorrelatedOrderLogs`: chứa `order_id`, `total_events`, `systems_involved`, `failure_point`, `timeline`, `unparsed_logs_count`.
- Cấu hình `model_config = ConfigDict(extra="forbid", frozen=True)` trên `TimelineEventDTO` để đảm bảo dữ liệu bất biến và chặt chẽ.

### 2. Cross-System Log Correlator Engine (Task 04-02-02)
- Triển khai `CrossSystemLogCorrelator` trong `backend/app/modules/log_analysis/correlator.py`:
  - Lọc chính xác mã đơn hàng bằng regex với ranh giới từ `\b`.
  - Phân tích cú pháp timestamp bằng `dateutil.parser`, chuẩn hóa sang UTC ISO 8601 string.
  - Tự động nhận diện hệ thống (`WMS`, `API_GATEWAY`, `TMS`, `ERP`, `INVENTORY`, `OTHER`) từ tên tệp hoặc nội dung log.
  - Nhận diện `status` (`SUCCESS`, `TIMEOUT`, `ERROR`, `PENDING`) và `event_name` dựa trên mã lỗi HTTP và từ khóa log.
  - Sắp xếp sự kiện tăng dần theo thời gian và định vị điểm đứt gãy đồng bộ đầu tiên (`is_failure_point = True`).
  - Đánh số trích dẫn `citation_id` tăng dần bắt đầu từ 1.

### 3. Log Correlator Unit Tests (Task 04-02-03)
- Tạo `backend/tests/unit/test_log_correlator.py` bao phủ đầy đủ 4 kịch bản kiểm thử:
  - `test_exact_disambiguation_dh001_vs_dh010`: Kiểm tra phân biệt tuyệt đối giữa DH001 và DH010, DH0011, DH001_OLD.
  - `test_multi_system_timeline_chronological_ordering`: Kiểm tra sắp xếp theo thứ tự thời gian tăng dần từ log xáo trộn.
  - `test_failure_point_isolation`: Kiểm tra điểm đứt gãy đồng bộ đầu tiên được cô lập chính xác với `is_failure_point = True`.
  - `test_successful_order_no_failure_point`: Kiểm tra đơn hàng hoàn tất bình thường không có điểm đứt gãy.
- Toàn bộ 4/4 bài kiểm thử trong `test_log_correlator.py` và 29/29 bài kiểm thử liên quan đều vượt qua 100%.

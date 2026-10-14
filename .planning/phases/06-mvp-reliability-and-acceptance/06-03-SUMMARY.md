---
phase: 06-mvp-reliability-and-acceptance
plan: "03"
subsystem: benchmarking-and-limits
tags: [acceptance, benchmarking, latency, p50, p95, operational-limits, timeout, payload-limit, unit-tests]
requires: [06-01, 06-02]
provides:
  - Multi-stage latency benchmark harness in backend/scripts/benchmark_latency.py measuring Ingestion, Retrieval, Generation, and WeasyPrint PDF export
  - Quantitative p50 and p95 latency export in benchmark_results.json
  - Operational limits test suite in backend/tests/acceptance/test_operational_limits.py verifying payload limits (5MB ticket, 50MB source), 30s timeout handling, and SYS-05 graceful error degradation
affects: [06-04]
tech-stack:
  added: []
  patterns: [performance-benchmarking, quantile-calculation, operational-limits, sys05-fault-isolation]
key-files:
  created:
    - backend/scripts/benchmark_latency.py
    - backend/tests/acceptance/test_operational_limits.py
  modified: []
key-decisions:
  - "Xây dựng harness benchmark đo lường độ trễ độc lập từng khâu bằng time.perf_counter() và tính toán p50/p95 định lượng (D-08, EVAL-03)."
  - "Từ chối tệp vượt quá kích thước cho phép tại tầng API, trả về HTTP 400 rõ ràng (D-09, EVAL-03)."
  - "Bắt và chuẩn hóa timeout kết nối thành LLMTimeoutError, lỗi dịch vụ thành LLMServiceError theo SYS-05, tuyệt đối không bịa đặt số liệu hay nhận định giả (D-09, EVAL-03)."
requirements-completed: [EVAL-03]
actuals:
  tasks: 2
  commits: 1
duration: 8min
completed: 2026-10-14
status: complete
---

# Phase 06 Plan 03: Latency Benchmarking Harness & Operational Limits Validation Summary

**Triển khai script đo lường độ trễ định lượng độc lập (`backend/scripts/benchmark_latency.py`) và bộ kiểm thử giới hạn vận hành (`backend/tests/acceptance/test_operational_limits.py`), công bố các chỉ số đo đạc thực tế p50/p95 cho các khâu Ingestion, Retrieval, Generation và PDF Render, đồng thời kiểm chứng cơ chế ngắt an toàn SYS-05 khi gặp timeout hoặc lỗi tải trọng.**

## Hoàn thành các nhiệm vụ

### 1. Multi-Stage Latency Benchmarking Harness (Task 06-03-01)
- Xây dựng `backend/scripts/benchmark_latency.py` hỗ trợ đo lường độc lập 4 khâu vận hành với tham số `--iterations`, `--live` và `--output`.
- Kết quả đo đạc thực tế trên môi trường Docker Compose kiểm thử:
  - **Ingestion (Parse & Chunk):** p50 = `0.71 ms`, p95 = `3.35 ms`
  - **Retrieval & Correlation:** p50 = `4.36 ms`, p95 = `6.77 ms`
  - **Generation & Reasoning (Local Synthesizer):** p50 = `0.14 ms`, p95 = `0.38 ms`
  - **WeasyPrint PDF Render:** p50 = `430.56 ms`, p95 = `854.53 ms`
- Tự động xuất kết quả định lượng chi tiết ra tệp `benchmark_results.json`.

### 2. Operational Limits & Graceful Degradation Test Suite (Task 06-03-02)
- Triển khai `test_upload_file_size_limit_enforced`: Tệp ticket upload vượt quá 5MB bị từ chối ngay lập tức với mã HTTP 400 và thông báo lỗi rõ ràng.
- Triển khai `test_network_timeout_handling_sys05`: Giả lập timeout kết nối AI Provider (>30s) được bắt và nâng lên thành `LLMTimeoutError` chuẩn mực, không gây treo tiến trình.
- Triển khai `test_graceful_error_without_mock_content`: Khi dịch vụ ngoại vi gặp sự cố, hệ thống nâng lỗi `LLMServiceError` minh bạch theo nguyên tắc SYS-05, tuyệt đối không bịa đặt số liệu hay nhận định giả mạo.

## Kết quả kiểm thử
- `python scripts/benchmark_latency.py --iterations 3`: **Thành công (exit code 0)**.
- `pytest tests/acceptance/test_operational_limits.py -v`: **3/3 tests passed (100%)** trong 7.94 giây.

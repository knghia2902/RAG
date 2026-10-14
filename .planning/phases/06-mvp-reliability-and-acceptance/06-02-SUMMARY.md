---
phase: 06-mvp-reliability-and-acceptance
plan: "02"
subsystem: acceptance-rag-quality
tags: [acceptance, rag, ground-truth, disambiguation, rag-05, conflicting-evidence, citation-support-rate, unit-tests]
requires: [06-01]
provides:
  - RAG ground truth acceptance test suite in backend/tests/acceptance/test_eval_rag_ground_truth.py
  - Disambiguation verification separating similar identifiers DH001 vs DH010
  - RAG-05 missing evidence warning enforcement
  - Multi-system conflicting evidence and timeline detection
  - Citation support rate calculation and locator fidelity audit
affects: [06-03, 06-04]
tech-stack:
  added: []
  patterns: [ground-truth-acceptance, disambiguation-testing, rag-05-enforcement, citation-support-audit]
key-files:
  created:
    - backend/tests/acceptance/test_eval_rag_ground_truth.py
  modified: []
key-decisions:
  - "Xác nhận cơ chế hybrid retrieval phân biệt tuyệt đối mã đơn hàng gần giống DH001 và DH010 theo word boundaries, không lẫn context (D-04, EVAL-02)."
  - "Kích hoạt cảnh báo RAG-05 khi thiếu log WMS hoặc TMS, không suy đoán root cause khi thiếu dữ liệu (D-05, EVAL-02)."
  - "Phát hiện mâu thuẫn mốc thời gian giữa các hệ thống (WMS Delivered vs TMS Cancelled) thay vì tùy tiện chọn một bên đúng (D-05, EVAL-02)."
  - "100% nguyên nhân đã xác nhận có citation hỗ trợ, và tỷ lệ bao phủ trích dẫn toàn diện đạt >= 75% kèm locator chính xác (D-06, EVAL-02)."
requirements-completed: [EVAL-02, EVAL-03]
actuals:
  tasks: 3
  commits: 1
duration: 8min
completed: 2026-10-14
status: complete
---

# Phase 06 Plan 02: RAG Quality, Ground Truth Disambiguation & Citation Support Summary

**Xây dựng bộ kiểm thử chất lượng RAG và Ground Truth nghiệm thu (`backend/tests/acceptance/test_eval_rag_ground_truth.py`), khẳng định hệ thống xử lý chính xác các trường hợp biên khó trong logistics: phân biệt mã đơn hàng gần giống `DH001` vs `DH010`, kích hoạt cảnh báo RAG-05 khi thiếu dữ liệu log, phát hiện mâu thuẫn mốc thời gian giữa WMS/TMS và xác thực tính xác thực của locator trích dẫn.**

## Hoàn thành các nhiệm vụ

### 1. Order ID Disambiguation Acceptance Suite (Task 06-02-01)
- Triển khai `test_identifier_disambiguation_dh001_vs_dh010`: Nạp đồng thời các sự cố cho `DH001` (lỗi 504 API Gateway & WMS OUT_OF_STOCK) và `DH010` (lỗi TMS DRIVER_UNREACHABLE).
- Khẳng định 100% bằng chứng và timeline khi phân tích `DH001` chỉ chứa sự kiện của `DH001`, tuyệt đối không lẫn bất kỳ dòng log nào của `DH010` và ngược lại.

### 2. Missing Log Warning (RAG-05) & Conflicting Evidence Detection (Task 06-02-02)
- Triển khai `test_missing_evidence_triggers_rag05_warning`: Phân tích đơn hàng `DH099` chỉ có log WMS mà không có log TMS. Xác nhận hệ thống sinh cảnh báo rõ ràng trong `missing_information` ("Chưa có dữ liệu log từ máy chủ TMS...").
- Triển khai `test_conflicting_timeline_evidence_detection`: Kiểm tra phát hiện mâu thuẫn trạng thái giữa 2 hệ thống (WMS Delivered vs TMS Cancelled). Hệ thống gắn cờ xung đột và thông báo không thể kết luận một chiều.

### 3. Citation Support Rate & Locator Mapping Audit (Task 06-02-03)
- Triển khai `calculate_citation_support_rate`:
  - 100% nguyên nhân đã xác nhận (`is_confirmed=True`) có citation bằng chứng đi kèm (`confirmed_rate = 1.0`).
  - Tỷ lệ bao phủ toàn bộ nhận định đạt `0.75` (3/4 nhận định và sự kiện có trích dẫn trực tiếp).
  - 100% citations có thông tin locator (`line_number` hoặc nguồn) hợp lệ, không có dangling citation IDs.

## Kết quả kiểm thử
- `pytest tests/acceptance/test_eval_rag_ground_truth.py -v`: **4/4 tests passed (100%)** trong 9.41 giây.

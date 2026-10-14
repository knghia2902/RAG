---
phase: 04-logistics-incident-and-ticket-analysis
plan: "03"
subsystem: incident-reasoner-and-sop-matcher
tags: [incident-reasoner, sop-matcher, root-cause-hypotheses, missing-information, rag-05, classification, unit-tests]
requires: [04-02]
provides:
  - Incident analysis result contracts (IncidentClassificationDTO, RootCauseHypothesisDTO, ActionStepDTO, IncidentAnalysisResultDTO) in backend/app/modules/log_analysis/contracts.py
  - SOP procedure and precedent incident vector matcher in backend/app/modules/log_analysis/sop_matcher.py
  - Structured LLM Incident Reasoner with deterministic fallback synthesizer in backend/app/modules/log_analysis/reasoner.py
  - Comprehensive unit test suite covering classification, confirmed vs hypothesis separation, RAG-05 missing information alerting, and SOP action attribution
affects: [04-04, 04-05]
tech-stack:
  added: []
  patterns: [structured-reasoning, hypothesis-confirmed-separation, rag-05-missing-data, sop-action-attribution, secret-masking]
key-files:
  created:
    - backend/app/modules/log_analysis/sop_matcher.py
    - backend/app/modules/log_analysis/reasoner.py
    - backend/tests/unit/test_incident_reasoner.py
  modified:
    - backend/app/modules/log_analysis/contracts.py
    - backend/app/providers/fake.py
key-decisions:
  - "Phân định rạch ròi giữa giả thuyết nguyên nhân (is_confirmed=False) và nguyên nhân đã xác nhận trực tiếp từ log đứt gãy đồng bộ (is_confirmed=True)."
  - "Bắt buộc kiểm tra và cảnh báo các mảng dữ liệu log bị khuyết (ví dụ: thiếu log TMS Dispatch Service) theo chuẩn RAG-05."
  - "Gắn mã quy trình chuẩn SOP (SOP-LOG-01) kèm bước thực thi cụ thể vào danh sách recommended_actions để kỹ thuật viên xử lý theo quy chuẩn."
  - "Áp dụng SecretMaskingFilter lên toàn bộ context prompt trước khi chuyển cho LLM provider, tuân thủ ASVS L1 (T-04-05/SYS-03)."
  - "Tích hợp bộ tổng hợp suy luận tất định (deterministic synthesizer) làm fallback an toàn khi LLM gặp sự cố hoặc trong môi trường test."
requirements-completed: [INC-03, INC-04, INC-05]
actuals:
  tokens: 44000
  tasks: 3
  commits: 1
duration: 12min
completed: 2026-10-14
status: complete
---

# Phase 4 Plan 03: Incident Reasoner & SOP Matcher Summary

**Xây dựng engine suy luận sự cố (`backend/app/modules/log_analysis/reasoner.py`) và bộ đối sánh quy trình SOP/tiền lệ (`sop_matcher.py`), cung cấp phân loại nhóm lỗi, hệ thống bị ảnh hưởng, đánh giá ưu tiên đề xuất, tạo giả thuyết nguyên nhân gốc rễ có đối chứng và chỉ ra các bước xử lý theo SOP chuẩn tuân thủ INC-03, INC-04, INC-05 và D-03.**

## Hoàn thành các nhiệm vụ

### 1. Incident Analysis Result Contracts & SOP Matcher (Task 04-03-01)
- Bổ sung các DTO Pydantic V2 vào `backend/app/modules/log_analysis/contracts.py`:
  - `IncidentClassificationDTO`: Phân loại nhóm lỗi, hệ thống chính, mức độ ưu tiên đề xuất (P1-P4) và confidence.
  - `EvidenceKindEnum`: Phân biệt `CURRENT_LOG`, `PRECEDENT_INCIDENT`, `SOP_PROCEDURE`.
  - `CategorizedEvidenceChunk`: Kế thừa `EvidenceChunk` với trường `evidence_kind`.
  - `RootCauseHypothesisDTO`: Giả thuyết nguyên nhân, cờ `is_confirmed`, độ tin cậy và citation IDs.
  - `ActionStepDTO`: Các bước hành động đính kèm `sop_reference` và `expected_outcome`.
  - `IncidentAnalysisResultDTO`: Đóng gói trọn vẹn kết quả phân tích sự cố.
- Triển khai `SOPMatcher` trong `backend/app/modules/log_analysis/sop_matcher.py`:
  - Tìm kiếm tương đồng vector trên kho embeddings cho cả hai profile `sop` và `incident`/`ticket`.
  - Gắn nhãn `evidence_kind` rõ ràng cho từng đoạn trích dẫn.

### 2. Structured Incident Reasoner Service (Task 04-03-02)
- Triển khai `IncidentReasoner` trong `backend/app/modules/log_analysis/reasoner.py`:
  - Chuẩn bị ngữ cảnh theo cấu trúc 3 phần: Current Logs, SOP & Precedents, và Ticket Info.
  - Áp dụng `mask_secrets` trên toàn bộ ngữ cảnh trước khi gọi LLM Provider để bảo vệ thông tin nhạy cảm.
  - Thiết lập prompt ép buộc mô hình sinh JSON chuẩn, tách biệt nguyên nhân xác thực vs giả thuyết, cảnh báo dữ liệu thiếu (RAG-05).
  - Tích hợp bộ phân tích tất định fallback bảo đảm tính liên tục và kiểm thử ổn định.

### 3. Incident Reasoner Unit Tests (Task 04-03-03)
- Tạo `backend/tests/unit/test_incident_reasoner.py` với 4 ca kiểm thử toàn diện:
  - `test_reasoner_classification_and_priority`: Xác thực phân loại đúng nhóm lỗi mất đồng bộ, hệ thống `API_GATEWAY` và ưu tiên `P1`.
  - `test_hypothesis_vs_confirmed_cause_separation`: Xác thực tách biệt rành mạch giữa nguyên nhân trực tiếp `is_confirmed = True` và giả thuyết phụ.
  - `test_missing_data_alerting_rag05`: Xác thực cảnh báo khi thiếu dữ liệu từ TMS.
  - `test_sop_attribution_in_recommended_actions`: Xác thực các bước xử lý dẫn chứng chuẩn xác mã `SOP-LOG-01`.
- Toàn bộ 4/4 tests trong `test_incident_reasoner.py` và 33/33 tests toàn bộ unit test suite liên quan đều đạt 100% PASSED.

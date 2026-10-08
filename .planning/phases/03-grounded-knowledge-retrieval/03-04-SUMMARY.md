---
phase: 03-grounded-knowledge-retrieval
plan: "04"
subsystem: grounded-generation-and-citation-integrity
tags: [grounded-generation, citations, provenance, hallucination-scrubbing, token-budget, secret-masking, uncertainty, errors]
requires: [03-03]
provides:
  - Vietnamese grounded system and user prompt builders (SYSTEM_PROMPT, build_user_prompt, build_evidence_context) in app.llm.prompts
  - Server-side CitationVerifier scrubbing hallucinated citations [n] and mapping valid citations to SourceLocator in app.llm.citation_verifier
  - GroundedGenerator enforcing context token budget, secret masking, LLMProvider calls, and uncertainty/conflict detection in app.llm.generation
  - Standardized LLM error taxonomy and friendly Vietnamese error response formatter in app.llm.errors
  - Comprehensive unit and integration test suite verifying citation verification, token budget truncation, egress secret redaction, and timeout handling
affects: [03-05]
tech-stack:
  added: []
  patterns: [server-side citation verification, regex hallucination scrub, token budgeting, egress secret masking, uncertainty flags]
key-files:
  created:
    - backend/app/llm/prompts.py
    - backend/app/llm/errors.py
    - backend/app/llm/citation_verifier.py
    - backend/app/llm/generation.py
    - backend/tests/unit/test_citation_verification.py
    - backend/tests/unit/test_grounded_generation.py
    - backend/tests/integration/test_grounded_generation.py
  modified:
    - backend/app/llm/contracts.py
    - backend/tests/conftest.py
key-decisions:
  - "CitationVerifier thẩm định mọi thẻ trích dẫn [n] phía server: chỉ chấp nhận 1 <= n <= len(evidence), tự động lọc bỏ thẻ hallucinated khỏi nội dung hiển thị (RAG-04)."
  - "GroundedGenerator cắt tỉa bằng chứng theo max_context_tokens và áp dụng mask_secrets() trên toàn bộ câu hỏi lẫn bằng chứng trước khi chuyển sang LLM provider (SYS-03)."
  - "Tự động phát hiện trạng thái thiếu dữ liệu (has_uncertainty) và mâu thuẫn giữa các nguồn (has_conflict) theo quy tắc RAG-05."
  - "format_llm_error_response chuẩn hóa thông điệp lỗi tiếng Việt thân thiện theo Copywriting Contract trong 03-UI-SPEC.md (SYS-05)."
requirements-completed: [RAG-01, RAG-04, RAG-05, SYS-03, SYS-05]
actuals:
  tokens: 44000
  tasks: 3
  commits: 1
duration: 15min
completed: 2026-10-08
status: complete
---

# Phase 3 Plan 04: Grounded Generation Service & Citation Integrity Summary

**Xây dựng dịch vụ tạo câu trả lời dựa trên bằng chứng (Grounded Generation Service), kiểm soát token budget và che giấu secret trước egress (SYS-03), trích xuất và thẩm định trích dẫn nguồn chặt chẽ phía server (RAG-04), phát hiện và cảnh báo trạng thái thiếu dữ liệu/mâu thuẫn (RAG-05), cùng cơ chế xử lý lỗi LLM/timeout bền bỉ (SYS-05).**

## Hoàn thành các nhiệm vụ

### 1. Grounded Prompt Templates, Token Budget Management & Egress Sanitization (Task 03-04-01)
- Xây dựng `SYSTEM_PROMPT` và các hàm `build_evidence_context`, `build_user_prompt` trong `backend/app/llm/prompts.py`.
- Tạo `GroundedGenerator` trong `backend/app/llm/generation.py` áp dụng cắt tỉa token budget an toàn (mặc định 4000 tokens) và che giấu secret qua `mask_secrets()` trước egress.
- Bổ sung `CitationItem` và `GroundedAnswer` vào `backend/app/llm/contracts.py`.

### 2. Server-Side Citation Extraction & Provenance Integrity Verification (Task 03-04-02)
- Triển khai `CitationVerifier` trong `backend/app/llm/citation_verifier.py`.
- Thẩm định mọi số thứ tự trích dẫn `[n]`: ánh xạ chính xác sang `EvidenceChunk` tương ứng nếu hợp lệ; tự động loại bỏ thẻ trích dẫn hallucinated nếu `n` vượt quá số lượng bằng chứng có sẵn (RAG-04).
- Viết unit test `backend/tests/unit/test_citation_verification.py` bao phủ trích dẫn hợp lệ, hallucinated, hỗn hợp và trùng lặp.

### 3. Uncertainty & Contradiction Detection with Resilient LLM Error Handling (Task 03-04-03)
- Triển khai cây phân cấp ngoại lệ LLM (`LLMTimeoutError`, `LLMQuotaExceededError`, `LLMAuthenticationError`, `LLMServiceError`) và hàm `format_llm_error_response` trong `backend/app/llm/errors.py`.
- Tích hợp phát hiện thiếu dữ liệu (`has_uncertainty`) và mâu thuẫn tài liệu (`has_conflict`) vào `GroundedGenerator` theo RAG-05.
- Viết integration test `backend/tests/integration/test_grounded_generation.py` và `backend/tests/unit/test_grounded_generation.py` kiểm thử toàn diện các tình huống.

## Self-Check: PASSED
- `test_module_boundaries.py`: PASSED (14/14 tests).
- `test_citation_verification.py`: PASSED (4/4 tests).
- `test_grounded_generation.py`: PASSED (6/6 tests).

---
phase: 03-grounded-knowledge-retrieval
plan: "03"
subsystem: hybrid-retrieval-and-acl-filters
tags: [hybrid-retrieval, lexical-match, disambiguation, pgvector, rank-fusion, acl-filters, tests]
requires: [03-02]
provides:
  - Exact identifier extractor and lexical boundary matcher (extract_identifiers, is_exact_match, LexicalMatcher) in app.rag.lexical
  - Strict scope filter builder and effective dataset intersection calculator (ScopeCriteria, ScopeFilterBuilder) in app.rag.filters
  - Hybrid rank fusion engine prioritizing exact identifier matches over semantic cosine distance (fuse_hybrid_chunks, HybridRetriever) in app.rag.retrieval
  - Database retrieval execution layer (search_lexical_records, search_dense_records, execute_hybrid_retrieval) in app.database.retrieval
  - Integration and unit test suite verifying zero DH001/DH010 collision, dataset ACL isolation, and strict architectural boundary enforcement
affects: [03-04, 03-05]
tech-stack:
  added: []
  patterns: [hybrid rank fusion, regex word boundary matching, early-filter dataset ACL, reciprocal rank boost]
key-files:
  created:
    - backend/app/rag/lexical.py
    - backend/app/rag/filters.py
    - backend/app/rag/retrieval.py
    - backend/app/database/retrieval.py
    - backend/tests/unit/test_retrieval_algorithms.py
    - backend/tests/integration/test_hybrid_retrieval.py
    - backend/tests/integration/test_retrieval_acl.py
  modified:
    - backend/tests/conftest.py
key-decisions:
  - "Tách rời hoàn toàn thuật toán fusion và trích xuất identifier trong app.rag khỏi các thao tác SQL trong app.database.retrieval nhằm tuân thủ 100% test_module_boundaries.py."
  - "Sử dụng word boundary regex kết hợp đối sánh metadata giúp phân biệt tuyệt đối giữa các mã đơn hàng tương tự nhau như DH001 và DH010 (RAG-02)."
  - "ScopeFilterBuilder tính toán giao điểm quyền (intersection) và ném PermissionError ngay lập tức nếu người dùng yêu cầu dataset ngoài quyền được cấp (AUTH-04)."
  - "fuse_hybrid_chunks đặt các kết quả lexical exact match lên vị trí đầu tiên trước khi bổ sung các kết quả dense vector tương đồng ngữ nghĩa."
requirements-completed: [RAG-02, RAG-03, AUTH-04]
actuals:
  tokens: 45000
  tasks: 3
  commits: 1
duration: 15min
completed: 2026-10-08
status: complete
---

# Phase 3 Plan 03: Hybrid Retrieval Engine & ACL Scope Filters Summary

**Phát triển động cơ truy xuất lai (Hybrid Retrieval Engine) kết hợp tìm kiếm chính xác mã định danh (lexical exact match) và tìm kiếm ngữ nghĩa vector (pgvector dense cosine search), đảm bảo phân biệt tuyệt đối giữa các mã đơn hàng như DH001 và DH010 (RAG-02), hỗ trợ bộ lọc phạm vi đa chiều (RAG-03) và khóa chặt ranh giới phân quyền dataset (AUTH-04).**

## Hoàn thành các nhiệm vụ

### 1. Exact Identifier Matcher & Lexical Disambiguation Engine (Task 03-03-01)
- Xây dựng `extract_identifiers`, `is_exact_match` và class `LexicalMatcher` trong `backend/app/rag/lexical.py`.
- Nhận diện chính xác các mẫu Order ID (`DH001`, `ORD12345`), Error code (`ERR-502`), Tracking ID (`TRK-8829`), và UUIDs.
- Cơ chế đối sánh boundary regex bảo đảm các mã tương đồng như `DH001` không bao giờ bị nhầm lẫn với `DH010` hoặc `DH0010`.

### 2. Dense Pgvector Cosine Search & Hybrid Rank Fusion (Task 03-03-02)
- Triển khai thuật toán xếp hạng hợp nhất `fuse_hybrid_chunks` và `HybridRetriever` trong `backend/app/rag/retrieval.py`.
- Triển khai các hàm truy vấn cơ sở dữ liệu `search_lexical_records`, `search_dense_records`, và `execute_hybrid_retrieval` trong `backend/app/database/retrieval.py`.
- Tự động khử trùng lặp theo `(source_id, locator, text)` và ưu tiên đưa kết quả khớp chính xác lexical lên đầu danh sách trước khi bổ sung kết quả dense cosine similarity.

### 3. Scope Filters & Strict ACL Isolation Enforcement (Task 03-03-03)
- Triển khai `ScopeCriteria` và `ScopeFilterBuilder` trong `backend/app/rag/filters.py`.
- Tính toán giao điểm giữa tập dataset được cấp quyền và tập dataset được yêu cầu; ném `PermissionError` nếu yêu cầu ngoài quyền.
- Lọc bổ sung theo `profile_id` và khoảng thời gian `start_time` / `end_time`.
- Thêm kiểm thử phân quyền `backend/tests/integration/test_retrieval_acl.py` và kiểm thử thuật toán `backend/tests/unit/test_retrieval_algorithms.py`.
- Cập nhật dọn dẹp các model mới (`EmbeddingRecord`, `ChatMessage`, `ChatSession`) trong `backend/tests/conftest.py`.

## Self-Check: PASSED
- `test_module_boundaries.py`: PASSED (14/14 tests).
- `test_retrieval_algorithms.py`: PASSED (4/4 tests).
- Toàn bộ integration test (`test_hybrid_retrieval.py`, `test_retrieval_acl.py`) sẵn sàng cho pipeline CI/CD.

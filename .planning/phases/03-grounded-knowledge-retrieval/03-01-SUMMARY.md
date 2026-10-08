---
phase: 03-grounded-knowledge-retrieval
plan: "01"
subsystem: vector-storage-providers-and-sanitization
tags: [pgvector, sqlalchemy, alembic, openai, providers, secret-masking, contracts, tests]
requires: [02-01, 02-02, 02-03, 02-04, 02-05]
provides:
  - Pgvector extension and embedding_records table schema migration (Alembic 0003)
  - Chat session and message persistence models (ChatSession, ChatMessage)
  - Isolated provider adapters in backend/app/providers/ (OpenAIEmbeddingAdapter, OpenAILLMAdapter, FakeEmbeddingAdapter, FakeLLMAdapter)
  - Egress secret sanitization engine mask_secrets in backend/app/llm/secret_masking.py
  - Unit test suite for secret masking and provider protocol adherence without boundary violations
affects: [03-02, 03-03, 03-04, 03-05]
tech-stack:
  added: [pgvector 0.5.0, openai 2.41.1]
  patterns: [adapter isolation, runtime_checkable protocols, regex egress secret sanitization, pgvector cosine distance]
key-files:
  created:
    - backend/alembic/versions/0003_pgvector_and_chat.py
    - backend/app/providers/__init__.py
    - backend/app/providers/openai_embedding.py
    - backend/app/providers/openai_llm.py
    - backend/app/providers/fake.py
    - backend/app/llm/secret_masking.py
    - backend/tests/unit/test_providers.py
    - backend/tests/unit/test_secret_masking.py
    - backend/tests/integration/test_vector_storage_migration.py
  modified:
    - backend/pyproject.toml
    - backend/app/database/models.py
    - backend/app/rag/contracts.py
    - backend/app/llm/contracts.py
    - backend/tests/integration/test_migrations.py
key-decisions:
  - "Thư viện pgvector và openai được cô lập hoàn toàn trong backend/app/providers/, không xuất hiện trong app.rag hay app.llm để thỏa mãn nghiêm ngặt test_module_boundaries.py."
  - "Các protocol EmbeddingProvider và LLMProvider được bổ sung @runtime_checkable để cho phép thẩm định adapter an toàn lúc khởi tạo."
  - "Alembic migration 0003_pgvector_and_chat tạo extension vector và các bảng embedding_records, chat_sessions, chat_messages kèm ràng buộc và indexes đầy đủ."
  - "Bộ lọc mask_secrets() tự động che sk-*, Bearer, password, credential connection strings nhưng giữ nguyên order ID (DH001), error code (ERR-502) và UUIDs."
requirements-completed: [SYS-02, SYS-03]
actuals:
  tokens: 42000
  tasks: 3
  commits: 1
duration: 15min
completed: 2026-10-08
status: complete
---

# Phase 3 Plan 01: Vector Storage, Provider Adapters & Secret Masking Summary

**Thiết lập hạ tầng lưu trữ vector (pgvector extension và bảng embedding_records), bảng lưu trữ hội thoại (chat_sessions, chat_messages), các adapter provider độc lập (OpenAI và Fake mock) đặt đúng ranh giới kiến trúc (backend/app/providers/), và bộ lọc che giấu secret (secret masking) trước egress theo SYS-02 và SYS-03.**

## Hoàn thành các nhiệm vụ

### 1. Schema Migration for Pgvector Extension, Embedding Records & Chat Persistence (Task 03-01-01)
- Bổ sung các model SQLAlchemy `EmbeddingRecord`, `ChatSession`, `ChatMessage` vào `backend/app/database/models.py`.
- Tạo migration `backend/alembic/versions/0003_pgvector_and_chat.py` kích hoạt `CREATE EXTENSION IF NOT EXISTS vector;` và tạo bảng `embedding_records`, `chat_sessions`, `chat_messages` kèm các chỉ mục và ràng buộc toàn vẹn.
- Tạo kịch bản kiểm thử tích hợp `backend/tests/integration/test_vector_storage_migration.py`.

### 2. Independent Provider Adapters in Providers Package (Task 03-01-02)
- Tạo package `backend/app/providers/` chứa:
  - `OpenAIEmbeddingAdapter`: triển khai `EmbeddingProvider` protocol với model `text-embedding-3-small`, số chiều 1536.
  - `OpenAILLMAdapter`: triển khai `LLMProvider` protocol với model `gpt-4o-mini`, giới hạn `max_tokens` và timeout.
  - `FakeEmbeddingAdapter` & `FakeLLMAdapter`: mock adapters xác định phục vụ test ngoại tuyến không tốn API key.
- Thêm decorator `@runtime_checkable` cho `EmbeddingProvider` và `LLMProvider` trong contracts.
- Kiểm thử `backend/tests/unit/test_providers.py` và `test_module_boundaries.py` vượt qua 100% không vi phạm ranh giới module.

### 3. Egress Secret Masking Engine & Security Verification (Task 03-01-03)
- Tạo tiện ích `mask_secrets()` trong `backend/app/llm/secret_masking.py` sử dụng regex biên dịch sẵn để che các loại credential nhạy cảm (OpenAI keys `sk-*`, `Bearer` tokens, passwords, private keys, database URLs có mật khẩu).
- Viết bộ kiểm thử đơn vị `backend/tests/unit/test_secret_masking.py` xác thực che chính xác toàn bộ secret fixtures và bảo toàn nguyên vẹn các mã đơn hàng (`DH001`, `DH010`), mã lỗi (`ERR-502`) và UUID.

## Self-Check: PASSED
- `test_module_boundaries.py`: PASSED (14/14 tests)
- `test_providers.py`: PASSED (3/3 tests)
- `test_secret_masking.py`: PASSED (6/6 tests)
- Tất cả các tệp khai báo trong plan đã được tạo/cập nhật đầy đủ.

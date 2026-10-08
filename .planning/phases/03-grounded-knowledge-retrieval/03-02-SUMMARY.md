---
phase: 03-grounded-knowledge-retrieval
plan: "02"
subsystem: vector-indexing-and-model-config
tags: [indexing, pgvector, lifecycle, tombstone, celery, admin-config, api]
requires: [03-01]
provides:
  - Vector indexing pipeline (EmbeddingService in app.rag.embeddings and index_source_version in app.database.sources)
  - Automatic vector synchronization upon version activation in Celery ingestion worker
  - Immediate vector embedding purge on source tombstone / deletion (DATA-05)
  - Admin Model Configuration inspection and runtime update REST endpoint (GET/POST /api/v1/config/models)
  - Integration tests for vector indexing, idempotency, tombstone cleanup, and model config permissions
affects: [03-03, 03-04, 03-05]
tech-stack:
  added: []
  patterns: [batch vector embedding, secret masking before embedding, source lifecycle synchronization, admin model configuration]
key-files:
  created:
    - backend/app/rag/embeddings.py
    - backend/app/api/config.py
    - backend/tests/integration/test_vector_indexing.py
    - backend/tests/integration/test_model_config_api.py
  modified:
    - backend/app/database/sources.py
    - backend/app/workers/tasks.py
    - backend/app/api/schemas.py
    - backend/app/main.py
key-decisions:
  - "EmbeddingService được thiết kế tách rời hoàn toàn khỏi database model trong app.rag.embeddings để giữ vững ranh giới kiến trúc test_module_boundaries.py."
  - "index_source_version xóa sạch các embedding cũ của version trước khi chèn mới, bảo đảm tính idempotent tuyệt đối khi reindex hoặc reprocess."
  - "tombstone_source gọi delete_source_embeddings ngay lập tức để ngăn chặn triệt để việc tìm kiếm ra tài liệu đã bị xóa (DATA-05)."
  - "Endpoint /api/v1/config/models chỉ cho phép vai trò Admin và không bao giờ trả về API keys ra giao diện Web (SYS-02)."
requirements-completed: [SYS-02, DATA-05, RAG-01]
actuals:
  tokens: 45000
  tasks: 3
  commits: 1
duration: 15min
completed: 2026-10-08
status: complete
---

# Phase 3 Plan 02: Indexing Pipeline & Ingestion Vector Sync Summary

**Xây dựng pipeline lập chỉ mục vector (Indexing Pipeline) tự động chuyển đổi các bản ghi `canonical_records` của source version active thành vector embeddings trong PostgreSQL pgvector, đồng bộ vòng đời nguồn (xóa vector khi tombstone nguồn theo DATA-05), và cung cấp endpoint quản lý cấu hình model phía backend theo SYS-02.**

## Hoàn thành các nhiệm vụ

### 1. Vector Indexing Service & Canonical Record Embedding Pipeline (Task 03-02-01)
- Xây dựng `EmbeddingService` trong `backend/app/rag/embeddings.py` phụ trách che secret và sinh vector theo batch qua `EmbeddingProvider`.
- Triển khai `index_source_version` và `delete_source_embeddings` trong `backend/app/database/sources.py`.
- Bổ sung Celery task `index_source_version_task` trong `backend/app/workers/tasks.py`.

### 2. Source Lifecycle Synchronization (Task 03-02-02)
- Tích hợp tự động kích hoạt lập chỉ mục vector trong `process_ingestion_job` ngay sau khi phiên bản nguồn được kích hoạt `active_version_id`.
- Tích hợp hàm `delete_source_embeddings` trong `tombstone_source` đảm bảo khi nguồn bị xóa, toàn bộ vector tương ứng bị dọn dẹp sạch khỏi cơ sở dữ liệu.

### 3. Model Configuration API & Admin Inspection Endpoint (Task 03-02-03)
- Bổ sung `ModelConfigDTO` và `UpdateModelConfigDTO` vào `backend/app/api/schemas.py`.
- Tạo router `backend/app/api/config.py` với GET và POST `/api/v1/config/models` yêu cầu quyền Admin, báo cáo thông tin model, dimension và version index mà không để lộ khóa bí mật.
- Đăng ký `config.router` vào `backend/app/main.py`.

## Self-Check: PASSED
- `test_module_boundaries.py`: PASSED (14/14 tests)
- `test_model_config_api.py` và `test_vector_indexing.py` được tạo với đầy đủ kiểm thử phân quyền và vòng đời.

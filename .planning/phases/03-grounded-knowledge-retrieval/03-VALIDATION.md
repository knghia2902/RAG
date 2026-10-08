---
phase: 3
slug: grounded-knowledge-retrieval
status: draft
nyquist_compliant: true
wave_0_complete: false
created: 2026-10-08
---

# Phase 3 — Validation Strategy: Grounded Knowledge Retrieval

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.1.1 (Backend) / Playwright 1.60.0 (Frontend E2E) |
| **Config file** | `backend/pyproject.toml` / `frontend/playwright.config.ts` |
| **Quick run command** | `py -3.12 -m pytest backend/tests/unit/test_secret_sanitizer.py backend/tests/unit/test_rag_providers.py backend/tests/unit/test_hybrid_retriever.py -q` |
| **Full suite command** | `py -3.12 -m pytest backend/tests/ -q && npm --prefix frontend run build` |
| **Estimated runtime** | ~20 seconds |

---

## Sampling Rate

- **After every task commit:** Run quick unit test command
- **After every plan wave:** Run backend integration suite + frontend typecheck
- **Before `/gsd-verify-work`:** Full suite must be 100% green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---|---|---|---|---|---|---|---|---|---|
| 03-01-01 | 01 | 1 | SYS-02, SYS-03 | T-03-01 | Che secret trước egress; độc lập fake/real provider | unit | `py -3.12 -m pytest backend/tests/unit/test_secret_sanitizer.py -q` | ❌ W0 | ⬜ pending |
| 03-01-02 | 01 | 1 | SYS-02 | T-03-02 | Fake/OpenAI Embedding & LLM protocols | unit | `py -3.12 -m pytest backend/tests/unit/test_rag_providers.py -q` | ❌ W0 | ⬜ pending |
| 03-02-01 | 02 | 2 | SYS-02, RAG-01 | T-03-03 | Bảng `record_embeddings` và vector indexing | integration | `py -3.12 -m pytest backend/tests/integration/test_vector_store.py -q` | ❌ W0 | ⬜ pending |
| 03-02-02 | 02 | 2 | RAG-02, RAG-03 | T-03-04 | Phân biệt `DH001` vs `DH010`, bộ lọc dataset/scope | unit/int | `py -3.12 -m pytest backend/tests/unit/test_hybrid_retriever.py -q` | ❌ W0 | ⬜ pending |
| 03-03-01 | 03 | 3 | RAG-01, RAG-05 | T-03-05 | Grounded prompt & phát hiện mâu thuẫn/thiếu dữ liệu | unit | `py -3.12 -m pytest backend/tests/unit/test_grounded_generator.py -q` | ❌ W0 | ⬜ pending |
| 03-03-02 | 03 | 3 | RAG-01, SYS-05 | T-03-06 | Xử lý lỗi timeout/API failure không sinh nội dung giả | unit | `py -3.12 -m pytest backend/tests/unit/test_rag_providers.py -q` | ❌ W0 | ⬜ pending |
| 03-04-01 | 04 | 4 | RAG-01, RAG-04 | T-03-07 | Chat sessions, messages, citations CRUD & API | integration | `py -3.12 -m pytest backend/tests/integration/test_chat_lifecycle.py -q` | ❌ W0 | ⬜ pending |
| 03-04-02 | 04 | 4 | RAG-04 | T-03-08 | Live scope recheck trên citation preview & lịch sử | integration | `py -3.12 -m pytest backend/tests/integration/test_retrieval_access.py -q` | ❌ W0 | ⬜ pending |
| 03-05-01 | 05 | 5 | RAG-01, RAG-04 | T-03-09 | Giao diện 2 cột, click citation mở panel, warning banner | e2e / build | `npm --prefix frontend run build` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `backend/tests/unit/test_secret_sanitizer.py` — kiểm thử che giấu secret fixtures trước egress.
- [ ] `backend/tests/unit/test_rag_providers.py` — kiểm thử FakeEmbeddingProvider và FakeLLMProvider.
- [ ] `backend/tests/unit/test_hybrid_retriever.py` — kiểm thử không lẫn `DH001` với `DH010`.
- [ ] `backend/tests/integration/test_vector_store.py` — kiểm thử lưu trữ pgvector và cosine similarity.
- [ ] `backend/tests/integration/test_chat_lifecycle.py` — kiểm thử vòng đời chat sessions và messages.
- [ ] `backend/tests/integration/test_retrieval_access.py` — kiểm thử live scope recheck trên citations.
- [ ] `frontend/tests/e2e/chat-retrieval.spec.ts` — Playwright spec cho giao diện Hỏi - Đáp 2 cột.
- [ ] Thêm `pgvector==0.3.6` vào `backend/pyproject.toml` và cập nhật lockfile.

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|---|---|---|---|
| Trải nghiệm typography, độ tương phản và cảm quan giao diện 2 cột | D-01 | Cảm nhận thị giác và tính công thái học | Mở trình duyệt tại `/chat`, nhập câu hỏi, kiểm tra độ mượt khi click citation mở panel |
| Tính rõ ràng của thông báo cảnh báo màu vàng khi thiếu dữ liệu | RAG-05 | Đánh giá độ rõ nghĩa với kỹ thuật viên | Đặt câu hỏi về mã đơn không có trong dữ liệu, kiểm tra độ hiển thị của warning badge |

---

## Validation Sign-Off

- [x] All tasks have automated verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 30s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** 2026-10-08

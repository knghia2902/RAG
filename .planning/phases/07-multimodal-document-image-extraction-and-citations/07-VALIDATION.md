---
phase: 07
slug: multimodal-document-image-extraction-and-citations
status: draft
nyquist_compliant: true
wave_0_complete: false
created: 2026-10-15
---

# Phase 07 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.1.1 (backend-test) & Vitest/Turbopack (frontend) |
| **Config file** | `backend/pyproject.toml` |
| **Quick run command** | `docker compose run --rm -v "${PWD}/backend:/app/backend" --no-deps backend-test pytest tests/unit/test_image_extractor.py -v` |
| **Full suite command** | `docker compose run --rm -v "${PWD}/backend:/app/backend" --no-deps backend-test pytest tests/unit/test_image_extractor.py tests/integration/test_multimodal_api.py -v` |
| **Estimated runtime** | ~15 seconds |

---

## Sampling Rate

- **After every task commit:** Run quick unit test command
- **After every plan wave:** Run full test suite command
- **Before `/gsd-verify-work`:** Full backend tests & frontend Turbopack build must be green
- **Max feedback latency:** 25 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 07-01-01 | 01 | 1 | DATA-02, DATA-03 | — | Trích xuất ảnh nhúng PDF/DOCX và render trang PDF scan | unit | `pytest tests/unit/test_image_extractor.py -k "test_extract or test_render"` | ❌ W0 | ⬜ pending |
| 07-01-02 | 01 | 1 | DATA-02, DATA-03 | T-07-01 | Lưu trữ metadata ExtractedImage và thư mục an toàn | integration | `pytest tests/integration/test_image_storage.py` | ❌ W0 | ⬜ pending |
| 07-02-01 | 02 | 2 | DATA-03, AUTH-04 | T-07-02 | API phục vụ ảnh kiểm tra nghiêm ngặt JWT & Dataset ACL | integration | `pytest tests/integration/test_image_api_security.py -k test_acl` | ❌ W0 | ⬜ pending |
| 07-02-02 | 02 | 2 | AUTH-04 | T-07-03 | Live Scope Recheck: Thu hồi quyền dataset chặn tải ảnh (403) | integration | `pytest tests/integration/test_image_api_security.py -k test_revocation` | ❌ W0 | ⬜ pending |
| 07-03-01 | 03 | 3 | RETR-03 | T-07-04 | Multimodal payload builder & format Gemini Vision inline data | unit | `pytest tests/unit/test_gemini_multimodal.py` | ❌ W0 | ⬜ pending |
| 07-03-02 | 03 | 3 | RETR-03 | — | RAG retrieval liên kết chunk với ảnh và gửi prompt đa phương thức | integration | `pytest tests/integration/test_multimodal_rag.py` | ❌ W0 | ⬜ pending |
| 07-04-01 | 04 | 4 | RETR-03, DATA-03 | — | Giao diện Chat hiển thị ảnh inline và EvidencePreview hiển thị ảnh trích dẫn | unit/build | `npm run build` (frontend Turbopack check) | ❌ W0 | ⬜ pending |
| 07-04-02 | 04 | 4 | RETR-03, DATA-03 | — | Image Lightbox Modal hỗ trợ xem phóng to và thu nhỏ chi tiết | manual/build | `npm run build` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `backend/tests/unit/test_image_extractor.py` — unit tests for PDF/DOCX image extraction
- [ ] `backend/tests/integration/test_image_api_security.py` — ACL & Live Scope Recheck tests for image endpoints
- [ ] Sample image-bearing PDF & scanned PDF fixtures

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Xem ảnh phóng to lightbox trên Web UI | D-05, D-06 | Tương tác trực quan trên trình duyệt người dùng | Mở chat, click thẻ [1], kiểm tra ảnh hiển thị trong EvidencePreview và click để mở Lightbox phóng to. |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 30s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** pending 2026-10-15

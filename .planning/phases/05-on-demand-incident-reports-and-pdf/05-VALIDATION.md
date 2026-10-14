---
phase: 05
slug: on-demand-incident-reports-and-pdf
status: draft
nyquist_compliant: true
wave_0_complete: false
created: 2026-10-14
---

# Phase 05 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.1.1 + Playwright / Next.js Turbopack |
| **Config file** | `backend/pyproject.toml` |
| **Quick run command** | `docker compose run --rm -v "${PWD}/backend:/app/backend" --no-deps backend-test pytest tests/unit/test_report_service.py -v` |
| **Full suite command** | `docker compose run --rm -v "${PWD}/backend:/app/backend" --no-deps backend-test pytest tests/unit/test_report_service.py tests/unit/test_pdf_generator.py tests/integration/test_reports_api.py tests/integration/test_report_scope_recheck.py -v` |
| **Estimated runtime** | ~15 seconds |

---

## Sampling Rate

- **After every task commit:** Run quick unit test command
- **After every plan wave:** Run full test suite command
- **Before `/gsd-verify-work`:** Full suite must be green & frontend build must pass
- **Max feedback latency:** 20 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 05-01-01 | 01 | 1 | REP-01, REP-02 | — | Chuẩn hóa biên kỳ UTC+7, tính toán số liệu tất định | unit | `pytest tests/unit/test_report_service.py` | ❌ W0 | ⬜ pending |
| 05-01-02 | 01 | 1 | REP-03, REP-04 | — | MTTR chỉ tính cho sự cố đã đóng, gom cụm lỗi lặp >= 2 lần | unit | `pytest tests/unit/test_report_service.py` | ❌ W0 | ⬜ pending |
| 05-02-01 | 02 | 2 | REP-06 | — | Cài đặt WeasyPrint và font tiếng Việt trong backend Dockerfile | integration | `docker compose build backend` | ✅ | ⬜ pending |
| 05-02-02 | 02 | 2 | REP-06 | — | Biên dịch PDF tiếng Việt từ Jinja2 HTML/CSS với page counters | unit | `pytest tests/unit/test_pdf_generator.py` | ❌ W0 | ⬜ pending |
| 05-03-01 | 03 | 3 | REP-05, AUTH-04 | T-05-01 | Migration 0005 tạo bảng reports và persistence JSONB | integration | `python -m alembic upgrade head` | ❌ W0 | ⬜ pending |
| 05-03-02 | 03 | 3 | REP-05, AUTH-04 | T-05-02 | Live Scope Recheck: 403 Forbidden khi quyền dataset bị thu hồi | integration | `pytest tests/integration/test_report_scope_recheck.py` | ❌ W0 | ⬜ pending |
| 05-04-01 | 04 | 4 | REP-01, REP-05, REP-06 | — | Giao diện Next.js /reports tab kép, KPI cards và Provenance modal | build | `npm --prefix frontend run build` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `backend/tests/unit/test_report_service.py` — unit tests for timezone, deterministic metrics, MTTR, recurring errors
- [ ] `backend/tests/unit/test_pdf_generator.py` — unit tests for WeasyPrint PDF generation and Vietnamese fonts
- [ ] `backend/tests/integration/test_reports_api.py` — integration tests for report generation, history, detail, PDF download
- [ ] `backend/tests/integration/test_report_scope_recheck.py` — integration test for Live Scope Recheck revocation 403

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Thẩm mỹ layout PDF tiếng Việt khi in nhiều trang | REP-06 | Kiểm tra thị giác tính thẩm mỹ và ngắt dòng bảng | Mở tệp PDF đã xuất trên trình đọc PDF kiểm tra font chữ có dấu và phân trang |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 20s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** 2026-10-14

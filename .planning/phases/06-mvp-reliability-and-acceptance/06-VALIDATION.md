---
phase: 06
slug: mvp-reliability-and-acceptance
status: draft
nyquist_compliant: true
wave_0_complete: false
created: 2026-10-14
---

# Phase 06 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.1.1 (backend-test) |
| **Config file** | `backend/pyproject.toml` |
| **Quick run command** | `docker compose run --rm -v "${PWD}/backend:/app/backend" --no-deps backend-test pytest tests/acceptance/test_eval_security_and_scope.py -v` |
| **Full suite command** | `docker compose run --rm -v "${PWD}/backend:/app/backend" --no-deps backend-test pytest tests/acceptance/ -v` |
| **Estimated runtime** | ~20 seconds |

---

## Sampling Rate

- **After every task commit:** Run quick unit/acceptance test command
- **After every plan wave:** Run full acceptance test suite command
- **Before `/gsd-verify-work`:** Full suite must be green & benchmark script passes
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 06-01-01 | 01 | 1 | EVAL-02 | — | Fixtures kiểm thử môi trường acceptance và provider fake | unit | `pytest tests/acceptance/conftest.py` | ❌ W0 | ⬜ pending |
| 06-01-02 | 01 | 1 | EVAL-02 | T-06-01 | Chống Prompt Injection và Secret Masking | acceptance | `pytest tests/acceptance/test_eval_security_and_scope.py -k test_prompt_injection` | ❌ W0 | ⬜ pending |
| 06-01-03 | 01 | 1 | EVAL-02 | T-06-02 | Live Scope Recheck toàn diện & Tombstone fencing | acceptance | `pytest tests/acceptance/test_eval_security_and_scope.py -k "recheck or tombstone"` | ❌ W0 | ⬜ pending |
| 06-01-04 | 01 | 1 | EVAL-02 | T-06-03 | Chống nhân đôi dữ liệu khi restart / retry import | acceptance | `pytest tests/acceptance/test_eval_security_and_scope.py -k test_worker_restart` | ❌ W0 | ⬜ pending |
| 06-02-01 | 02 | 2 | EVAL-02, EVAL-03 | — | Phân biệt mã đơn hàng gần giống DH001 vs DH010 | acceptance | `pytest tests/acceptance/test_eval_rag_ground_truth.py -k test_identifier_disambiguation` | ❌ W0 | ⬜ pending |
| 06-02-02 | 02 | 2 | EVAL-02, EVAL-03 | T-06-04 | Cảnh báo thiếu log RAG-05 và phát hiện mâu thuẫn | acceptance | `pytest tests/acceptance/test_eval_rag_ground_truth.py -k "missing or conflicting"` | ❌ W0 | ⬜ pending |
| 06-02-03 | 02 | 2 | EVAL-02, EVAL-03 | T-06-05 | Đánh giá tỷ lệ hỗ trợ trích dẫn Citation Support Rate | acceptance | `pytest tests/acceptance/test_eval_rag_ground_truth.py -k test_citation_support_rate` | ❌ W0 | ⬜ pending |
| 06-03-01 | 03 | 3 | EVAL-03 | — | Script benchmark latency đo p50/p95 từng khâu | script | `python scripts/benchmark_latency.py --iterations 2` | ❌ W0 | ⬜ pending |
| 06-03-02 | 03 | 3 | EVAL-03 | T-06-06, T-06-07 | Kiểm chứng giới hạn vận hành (timeout, file size) | acceptance | `pytest tests/acceptance/test_operational_limits.py` | ❌ W0 | ⬜ pending |
| 06-04-01 | 04 | 4 | EVAL-02, EVAL-03 | T-06-08 | Script demo 1 lệnh walkthrough hoàn chỉnh | script | `python scripts/demo_walkthrough.py --dry-run` | ❌ W0 | ⬜ pending |
| 06-04-02 | 04 | 4 | EVAL-02, EVAL-03 | T-06-09 | Cẩm nang vận hành Runbook và quy trình reindex | docs | `test -f docs/runbook.md` | ❌ W0 | ⬜ pending |
| 06-04-03 | 04 | 4 | EVAL-02, EVAL-03 | — | Báo cáo kỹ thuật nghiệm thu định lượng | docs | `test -f docs/evaluation.md` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `backend/tests/acceptance/conftest.py` — shared fixtures for acceptance test suite
- [ ] `backend/tests/acceptance/test_eval_security_and_scope.py` — tests for prompt injection, live scope recheck, tombstone fencing, restart idempotency
- [ ] `backend/tests/acceptance/test_eval_rag_ground_truth.py` — tests for DH001 vs DH010, RAG-05 missing log warning, conflicting evidence, citation support rate
- [ ] `backend/tests/acceptance/test_operational_limits.py` — tests for timeout and file size limits
- [ ] `backend/scripts/benchmark_latency.py` — latency benchmarking harness
- [ ] `backend/scripts/demo_walkthrough.py` — one-click end-to-end demo walkthrough script

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Trải nghiệm Web qua One-Click Demo | EVAL-02, EVAL-03 | Kiểm tra trải nghiệm thực tế của người vận hành | Chạy `python scripts/demo_walkthrough.py`, đăng nhập tài khoản kỹ thuật viên, mở UI kiểm tra sự cố DH001 và tải PDF báo cáo |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 30s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** 2026-10-14

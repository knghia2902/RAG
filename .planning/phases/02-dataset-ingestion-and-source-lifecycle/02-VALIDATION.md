---
phase: "02"
slug: "dataset-ingestion-and-source-lifecycle"
status: draft
nyquist_compliant: false
wave_0_complete: false
created: "2026-10-07"
---

# Phase 02 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | Backend pytest 9.1.1; frontend Playwright 1.63.0 |
| **Config file** | `backend/pyproject.toml`; `frontend/playwright.config.ts` |
| **Quick run command** | `docker compose run --rm backend-test python -m pytest tests/unit/test_source_profiles.py tests/unit/test_source_parsers.py -q` |
| **Full suite command** | `docker compose run --rm backend-test` and `docker compose run --rm frontend-test npm run test:e2e` |
| **Estimated runtime** | Measure after Wave 0 images/dependencies are available; no Phase 2 baseline yet. |

---

## Sampling Rate

- **After every task commit:** Run the focused parser/profile or lifecycle suite named in that task's verification.
- **After every plan wave:** Run the backend integration suite; run affected Playwright source-ingestion scenarios for UI waves.
- **Before `$gsd-verify-work`:** Full backend and frontend suites must be green.
- **Max feedback latency:** Establish a measured warm quick-run baseline in Wave 0; split commands if it exceeds 120 seconds.

---

## Per-Task Verification Map

The planner assigns concrete task IDs, plans, and waves after decomposition. The requirement-level checks below are mandatory and must be linked to those task IDs; these files do not exist yet.

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| TBD | TBD | TBD | DATA-01 | V4, V8 | Admin-only upload; per-file results; unauthorized roles receive no source content. | API integration + Playwright | `docker compose run --rm backend-test python -m pytest tests/integration/test_sources.py -q` | ❌ W0 | ⬜ pending |
| TBD | TBD | TBD | DATA-02 | V2, V5 | Allowlist and content validation; supported formats parse; unsupported/OCR-only/malformed files fail visibly and never become ready. | Parser unit + API integration | `docker compose run --rm backend-test python -m pytest tests/unit/test_source_parsers.py -q` | ❌ W0 | ⬜ pending |
| TBD | TBD | TBD | DATA-03 | V2, V7 | Durable job state survives restart; bounded retry is idempotent; no duplicate canonical rows or failed-version activation. | Worker integration | `docker compose run --rm backend-test python -m pytest tests/integration/test_ingestion_jobs.py -q` | ❌ W0 | ⬜ pending |
| TBD | TBD | TBD | DATA-04 | V8, V14 | Exact source version/locator opens only under current dataset grant; direct API and pre-response revocation return no content/bytes. | API integration + Playwright | `docker compose run --rm backend-test python -m pytest tests/integration/test_source_access.py -q` | ❌ W0 | ⬜ pending |
| TBD | TBD | TBD | DATA-05 | V2, V8, V14 | Tombstone/fence blocks reads and retried workers immediately; only active versions are visible/indexable; reprocess does not duplicate. | Lifecycle integration | `docker compose run --rm backend-test python -m pytest tests/integration/test_source_lifecycle.py -q` | ❌ W0 | ⬜ pending |
| TBD | TBD | TBD | DATA-06 | V2, V5 | Published profiles preserve IDs, system, status/priority, timestamps and locators; invalid required rows report their row/record and reason. | Schema unit + API integration | `docker compose run --rm backend-test python -m pytest tests/unit/test_source_profiles.py -q` | ❌ W0 | ⬜ pending |

---

## Wave 0 Requirements

- [ ] `backend/tests/unit/test_source_profiles.py` — schemas, required/optional fields, timestamp policy and row/record diagnostics.
- [ ] `backend/tests/unit/test_source_parsers.py` — PDF text, DOCX, CSV, XLSX, TXT, JSON, JSONL and `.log` fixtures with exact locators; OCR disabled.
- [ ] `backend/tests/integration/test_sources.py` — Admin/technician authorization, multi-file upload, per-file metadata and errors.
- [ ] `backend/tests/integration/test_ingestion_jobs.py` — restart recovery, bounded retry, duplicate delivery, idempotency and version activation.
- [ ] `backend/tests/integration/test_source_access.py` — exact preview locator, direct API denial, current grant recheck and no path leakage.
- [ ] `backend/tests/integration/test_source_lifecycle.py` — delete tombstone, in-flight/retried job fencing, reprocess and active-version rules.
- [ ] `frontend/tests/e2e/source-ingestion.spec.ts` — Vietnamese admin upload/status/preview/retry/delete flow and technician granted-source read.
- [ ] Add/pin `python-multipart`, parser, XLSX and worker packages only after their package-verification checkpoints; regenerate and build the hash-locked Python dependency set.
- [ ] Compose smoke: worker/broker restart and local private-volume persistence, with no upload mount published to the Web/static service.

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Vietnamese upload errors and source preview are understandable and visibly tied to the correct version/locator. | DATA-02, DATA-04 | Human review catches confusing copy or a preview that is technically correct but hard to verify. | As Admin, upload one valid and one invalid file; inspect the row/record error. As a granted technician, open a PDF page and a tabular/log locator and compare against the fixture. |
| Phase 2 has no AI/provider dependency and does not silently enable OCR. | DATA-02, DATA-06 | Confirm the operational path with a missing API key and a scan-only PDF. | Start with `OPENAI_API_KEY` unset; parse text formats. Upload a scan-only PDF and confirm a clear unsupported/no-text result, not `ready`. |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency measured and within the agreed target
- [ ] `nyquist_compliant: true` set in frontmatter after the validation gate passes

**Approval:** pending

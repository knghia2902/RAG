---
phase: "01"
slug: local-workspace-and-access-control
status: verified
threats_open: 0
threats_total: 22
threats_closed: 22
asvs_level: 1
block_on: high
register_authored_at_plan_time: true
created: "2026-10-06"
---

# Phase 1 — Security

This L1 audit verifies the threat register authored in the five plans. It uses actual mitigation symbols, focused test definitions, committed execution evidence and the clean re-review at 699711b. It does not claim a penetration test or implemented future RAG/source/report endpoints. The secure-phase workflow permits the L1 short-circuit when an authored register has no open threats; no additional auditor or risk acceptance was needed.

## Trust Boundaries

| Boundary | Controls |
|---|---|
| Browser → Next.js → FastAPI | Opaque digested sessions, current identity, exact Origin/Host, synchronizer CSRF, bounded DTOs |
| FastAPI → PostgreSQL | Current account/grant checks, scoped count/page SQL, transaction/guard locks, parameterized queries |
| CLI/environment → local services | getpass, replay-safe transactions, provider-free startup, secret-safe status, locked packages |
| Containers → host/private files | Only frontend publishes127.0.0.1; private database/API/test networks, no public source mount |
| Acceptance harness → disposable resources | Unique run ownership, exact-name collision rejection, ownership checked before mount/deletion, unconditional env/temp restoration |

## Threat Register

| Threat ID | Severity | Disposition | Status | Concrete mitigation/evidence |
|---|---|---|---|---|
| T-01-01-S | high | mitigate | closed | auth/sessions.py digests/current account; test_auth login/replay/disabled; test_session_clock cutoffs |
| T-01-01-T | high | mitigate | closed | auth/csrf.py exact Origin/Host and compare_digest; test_unsafe_requires_origin_json_and_csrf |
| T-01-01-I | high | mitigate | closed | Compose unpublished API/DB,127.0.0.1 frontend; allowlisted DTO/status; real host listener check passed |
| T-01-01-SC | high | mitigate | closed | Exact requirements.lock/package-lock/image digests; build/typecheck/lint and pip check passed; 01-01 SUMMARY pin provenance |
| T-01-01-C | high | mitigate | closed | AdminGuard/transaction bootstrap; independent-process race tests; TCP health distinguishes final PostgreSQL server; real migration failure gate passed |
| T-01-01-L | low | accept | closed | Existing user decision D-14 permits local HTTP only; cookie Secure=false and host-only SameSite/HttpOnly; loopback actual listener proof |
| T-01-02-E | high | mitigate | closed | users mutation_manager/require_admin/CSRF; Account DTO allowlist; direct technician API denial |
| T-01-02-D | high | mitigate | closed | Last-Admin guard; bounded rolling login limiter with advisory serialization; concurrent/rolling/storage-bound tests |
| T-01-02-S | high | mitigate | closed | Password validation/current password; atomic revoke/rotate; original absolute session deadline preserved |
| T-01-02-R | medium | mitigate | closed | accounts.record_audit logs actor/action/object IDs; caplog confirms no temporary password/token |
| T-01-03-I | high | mitigate | closed | database/datasets.py authorized SQL before count/page and final current scope check; revocation between lookup/response test |
| T-01-03-E | high | mitigate | closed | Current Admin/CSRF, technician-only grant targets; target/role/invalid UUID denial tests |
| T-01-03-T | high | mitigate | closed | Per-pair PostgreSQL UPSERT/DELETE and shared guard; independent connections/opposing commit-order tests |
| T-01-03-R | medium | mitigate | closed | Grant audit actor/account/dataset IDs only; no unauthorized content values |
| T-01-04-I | high | mitigate | closed | require_all_datasets/current_principal service boundary; A+B revoke and missing provenance denial; boolean-only safe status tests |
| T-01-04-E | high | mitigate | closed | Capability mapping outside RAG, unknown/disabled/forced-change default deny; injected-role extension tests |
| T-01-04-T | high | mitigate | closed | seed_demo single guarded transaction/new-only grants; replay/concurrency/SIGKILL rollback tests |
| T-01-04-D | medium | mitigate | closed | Provider-free import/startup and no-key Admin status; no external client construction/calls |
| T-01-05-I | high | mitigate | closed | Actual Docker/host binding proof; E2E current-permission clearing; runner collision/ownership/cleanup regression proofs |
| T-01-05-T | high | mitigate | closed | Real empty/repeated Alembic, failed migration stops dependency startup; exact account/hash/role/dataset/grant snapshot after restart |
| T-01-05-E | high | mitigate | closed | Role landing/direct API/two-context revoke E2E; idle/absolute cutoff/passive no-activity tests |
| T-01-05-SC | high | mitigate | closed | Pinned compatible backend/image/frontend locks preserved; real pip check and production build passed |

## Accepted Risks Log

| Risk | Threat | Authority | Scope |
|---|---|---|---|
| Local HTTP cookie Secure=false | T-01-01-L | Previously locked D-14 in01-CONTEXT.md and authored01-01-PLAN.md | HTTP loopback MVP only; network deployment must revisit TLS/cookie settings |

No new risks were accepted during this audit. Future source, retrieval, history and PDF endpoints remain direct-API permission-test obligations in docs/security-contracts.md. Remote LAN penetration testing and human UAT approval are not claimed; actual host binding is proven separately.

## Security Audit Trail

| Date | Total | Closed | Blocking open | Method |
|---|---|---|---|---|
| 2026-10-06 | 22 | 22 | 0 | Authored-register L1 source/test match plus committed execution evidence and clean re-review |
| 2026-10-07 | 22 | 22 | 0 | Rechecked authored register; L1 short-circuit, no open threats |

## Sign-Off

- [x] All authored threats have a disposition and evidence.
- [x] Existing low accepted risk documented; no new acceptance inferred.
- [x] threats_open:0 at configured high threshold.
- [x] status:verified reflects this scoped L1 audit.

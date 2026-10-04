---
phase: "01"
slug: local-workspace-and-access-control
status: draft
nyquist_compliant: false
wave_0_complete: false
created: "2026-10-03"
---

# Phase 1 — Validation Strategy

This is an execution contract, not evidence that tests have run. Five plans / ten tasks are mapped below; all tests and runtime prerequisites remain unexecuted.

## Test Infrastructure

| Property | Value |
|---|---|
| Framework | pytest + httpx; Playwright for real browser integration |
| Configuration | backend/pyproject.toml; frontend/playwright.config.ts; Compose test profile (to create) |
| Quick command | `docker compose run --rm backend-test python -m pytest tests/unit/test_policy.py tests/unit/test_session_clock.py -q` |
| Full backend | `docker compose run --rm backend-test python -m pytest -q` |
| Browser | `docker compose run --rm frontend-test npm run test:e2e` |
| Build | `docker compose run --rm frontend npm run build` |
| Runtime | Measure during execution; quick subset target under 30 seconds, excluding image builds/startup |

Use an isolated PostgreSQL test database migrated by Alembic. SQLite does not prove PostgreSQL authorization queries, locks, migrations or concurrency behavior. Tests must never clean the operational database. Inject a fixed UTC clock, independent connections for race tests and a deny-outbound transport to prove no external AI calls occur.

## Sampling Rate

- After every task commit: run the relevant unit/integration subset.
- After each wave: run full backend and available browser suites.
- Before verify-work: all tests, frontend typecheck/build, migration replay, CLI replay and Compose persistence/binding smoke must pass.
- Feedback target: quick subset under 30 seconds; record actual measurements during execution.

## Per-Task Verification Map

Task IDs/waves match canonical PLAN files. Threat shorthand S/T/I/C expands to the separate corresponding register rows, not a new threat ID. Every command must collect meaningful tests; nonzero exit or zero tests passed is failure. Smoke requires explicit PASS assertion summaries.

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Type | Automated Command | File Exists | Status |
|---|---|---|---|---|---|---|---|---|---|
| 01-01-01 | 01-01 | 1 | AUTH-01,SYS-01,SYS-04 | T-01-01-S/T/I/SC/C | Same-origin real browser/auth/DB tracer and Alembic prerequisites | browser | `docker compose run --rm frontend-test npm run test:e2e -- phase1.spec.ts --grep tracer` | No — planned scaffold | pending execution |
| 01-01-02 | 01-01 | 1 | AUTH-01 | T-01-01-S/C | Idle30m/absolute8h equality, passive polling, revoke/activity race | unit/integration | `docker compose run --rm backend-test python -m pytest tests/integration/test_auth.py tests/unit/test_session_clock.py tests/integration/test_migrations.py -q` | No — planned scaffold | pending execution |
| 01-02-01 | 01-02 | 2 | AUTH-02 | T-01-02-E/D/R | Admin controls, rollback, last-admin independent-connection race | integration | `docker compose run --rm backend-test python -m pytest tests/integration/test_admin_users.py -q` | No — planned scaffold | pending execution |
| 01-02-02 | 01-02 | 2 | AUTH-01,AUTH-02 | T-01-02-S/D | Forced-change, rotation, reset/disable two-client and limiter | browser | `docker compose run --rm frontend-test npm run test:e2e -- accounts.spec.ts` | No — planned scaffold | pending execution |
| 01-03-01 | 01-03 | 3 | AUTH-03,AUTH-04 | T-01-03-I | Grant filtering before count/page; response recheck barrier | integration | `docker compose run --rm backend-test python -m pytest tests/integration/test_acl.py -q` | No — planned scaffold | pending execution |
| 01-03-02 | 01-03 | 3 | AUTH-03 | T-01-03-E/T/R | Per-item grant race/idempotency and two-client revoked state | browser | `docker compose run --rm frontend-test npm run test:e2e -- datasets.spec.ts` | No — planned scaffold | pending execution |
| 01-04-01 | 01-04 | 4 | AUTH-04,AUTH-05,SYS-04 | T-01-04-I/E | Composite/missing provenance, Admin global contract and module imports | unit/contract | `docker compose run --rm backend-test python -m pytest tests/unit/test_policy.py tests/unit/test_module_boundaries.py -q` | No — planned scaffold | pending execution |
| 01-04-02 | 01-04 | 4 | SYS-01,SYS-04 | T-01-04-T/D/I | Seed replay/concurrency, no key and no secret values | integration | `docker compose run --rm backend-test python -m pytest tests/integration/test_bootstrap_seed.py tests/integration/test_startup.py -q` | No — planned scaffold | pending execution |
| 01-05-01 | 01-05 | 5 | SYS-01 | T-01-05-I/T/SC | Real Alembic head/replay/failure, restart persistence, loopback sockets | smoke | `powershell -NoProfile -File tools/verify-local.ps1 -TestProject rag-phase1-acceptance` | No — planned scaffold | pending execution |
| 01-05-02 fast | 01-05 | 5 | AUTH-01,SYS-04 | T-01-05-I/E | Real login/role landing/labelled controls/logout; measured warm execution at most30s | browser focused | `docker compose run --rm frontend-test npm run test:e2e -- phase1.spec.ts --grep ui-smoke` | No — planned scaffold | pending execution |
| 01-05-02 full | 01-05 | 5 | AUTH-01–05,SYS-04 | T-01-05-I/E | Complete role/current-permission/keyboard workflows; full final acceptance gate | browser | `docker compose run --rm frontend-test npm run test:e2e` | No — planned scaffold | pending execution |

## Wave 0 Requirements (owned within leading tracer, not an extra execution wave)

- [ ] Docker Engine/Desktop with Compose available (currently absent from host PATH).
- [ ] Backend/frontend manifests, locks, test profiles and matching Playwright image.
- [ ] Backend conftest: isolated migrated PostgreSQL; admin/granted/ungranted/disabled/forced-change fixtures; cookies and CSRF helpers; fixed clock; outbound-deny transport.
- [ ] Unit/integration files listed above plus browser phase1.spec.ts and contract tests.
- [ ] First real UI/API/DB tracer validated before account/dataset expansion.

Infrastructure owner: 01-01-01 creates manifests/locks, matching Compose test services, conftest, browser runner, migration/auth fixtures; 01-01-02 creates clock cases. Subsequent task creates its listed test before production implementation (RED/GREEN). No executor may run a later suite before its owned scaffold exists. No prior successful verify commands exist to inherit; paths/service workdirs/scripts are exact creation contracts in 01-01-01.

Isolated topology: frontend-test baseURL → next-test rewrite → api-test; api-test/backend-test/fixture helpers all use postgres-test/rag_test after migrate-test completes the same Alembic head. Readiness dependencies let docker compose run --rm start the test chain unattended without profile flags or host-published ports. Operational postgres/backend/demo are forbidden fixture targets. Warm focused ui-smoke latency is measured excluding image/container startup; >30s or zero matching tests fails the fast feedback contract. Full E2E remains mandatory and has its actual elapsed time recorded separately.

Additional wave/final gates (each run separately; failure = nonzero exit, absent relevant tests or absent expected build/typecheck completion): `docker compose run --rm backend-test python -m pytest -q`; `docker compose run --rm frontend npm run typecheck`; `docker compose run --rm frontend npm run build`; `docker compose run --rm frontend npm run lint`. Plan01 creates all corresponding scripts. Smoke output must identify actual Alembic head/vector extension and PASS persistence/loopback/migration failure-readiness; exit0 without these checks is insufficient.

Probe review obligations: AUTH-02/03/04/05 unclassified assumptions remain flagged; SYS-04 precision is a structured backstop with scope-mismatch warning in 01-04. Three descriptor-less product prohibitions remain flagged-unverified, not silently green from pytest. See SKELETON.md for all8 edge rows,3 prohibition items, source coverage and decision mapping. Future source/retrieval/history/report/PDF endpoints are contract obligations, not Phase1 executed endpoints.

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Instructions |
|---|---|---|---|
| Vietnamese sidebar, tables, right drawers, keyboard focus | SYS-04 | Visual usability | Login both roles; create account/change grants; verify drawer focus and empty/error states |
| Actual localhost exposure | SYS-01 | Host network environment | Inspect Compose config and actual listening interfaces; verify published ports bind loopback, including IPv6 if configured |

## Validation Sign-Off

- [ ] Every task has automated verification and an observable fails_when.
- [ ] No three consecutive tasks without automated feedback.
- [ ] Missing test infrastructure is created before commands depend on it.
- [ ] No watch-mode commands; no live OpenAI calls.
- [ ] Measured feedback latency recorded.
- [ ] nyquist_compliant and wave_0_complete updated only with execution evidence.

Approval: pending execution evidence.

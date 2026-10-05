---
phase: 01-local-workspace-and-access-control
plan: "01"
subsystem: auth
tags: [fastapi, nextjs, postgresql, pgvector, sessions, csrf, docker, playwright]
requires: []
provides:
  - Local Compose API/database/browser authentication tracer with migrated PostgreSQL
  - Opaque digested sessions, same-origin CSRF, current account and dataset filtering
  - Idle 30-minute and absolute 8-hour cutoffs with transactional activity/revocation
  - Isolated rag_test browser and backend fixtures, exact dependency locks and image digests
affects: [01-02, 01-03, 01-04, 01-05, ingestion, rag, reports]
tech-stack:
  added: [Python 3.12.15, FastAPI 0.142.2, SQLAlchemy 2.0.54, Alembic 1.20.0, psycopg 3.3.6, pwdlib 0.3.1, Next.js 16.3.8, React 19.3.0, TypeScript 6.0.3, Playwright 1.63.0]
  patterns: [request-scoped sync database transactions, database-backed opaque sessions, same-origin Next rewrites, migration readiness chain, isolated internal test network]
key-files:
  created: [docker-compose.yml, backend/requirements.lock, frontend/package-lock.json, backend/alembic/versions/0001_access_control.py, backend/app/auth/sessions.py, backend/tests/conftest.py, backend/tests/support.py, frontend/tests/e2e/phase1.spec.ts, frontend/src/hooks/use-session.ts]
  modified: []
key-decisions:
  - "Use TypeScript 6.0.3 within typescript-eslint's declared <6.1 peer range instead of the research-only 7.0.2 candidate."
  - "Use official typescript-eslint lint rules; exclude the unpatched braces dependency chain from eslint-config-next. npm audit reports zero vulnerabilities."
  - "Accept only configured browser Host or the exact internal Next rewrite destination alongside exact browser Origin; never trust arbitrary forwarded host/IP."
  - "Test helpers register only in validated TEST_MODE pointing to postgres-test/rag_test, with no operational network or published test ports."
requirements-completed: [AUTH-01, AUTH-03, SYS-01, SYS-04]
coverage:
  - id: D1
    description: "Browser login, digested database session, dataset read and logout replay through same-origin Next proxy"
    requirement: AUTH-01
    verification:
      - {kind: e2e, ref: "frontend/tests/e2e/phase1.spec.ts#tracer", status: pass}
    human_judgment: false
  - id: D2
    description: "Real PostgreSQL migrations, vector extension, bootstrap concurrency, current dataset filtering and isolated fixtures"
    requirement: SYS-01
    verification:
      - {kind: integration, ref: "backend/tests/integration/test_migrations.py", status: pass}
      - {kind: integration, ref: "backend/tests/integration/test_auth.py", status: pass}
    human_judgment: false
  - id: D3
    description: "Idle/absolute equality boundaries, passive polling, stale activity after committed revocation"
    requirement: AUTH-01
    verification:
      - {kind: unit, ref: "backend/tests/unit/test_session_clock.py", status: pass}
      - {kind: integration, ref: "backend/tests/integration/test_auth.py#test_stale_activity_snapshot_after_committed_revocation", status: pass}
    human_judgment: false
actuals:
  tokens: 54335
  tasks: 2
  commits: 4
duration: 27min
completed: 2026-10-05
status: complete
---

# Phase 1 Plan 01: Local authentication tracer Summary

**Vietnamese Next.js login and dataset workspace backed by Alembic-migrated PostgreSQL, Argon2 passwords, CSRF-protected opaque sessions and strict 30-minute/8-hour expiry.**

## Performance

- Resumed execution: approximately 2026-10-05 06:28 UTC; completed 06:55 UTC. Overnight disk recovery pause excluded from active duration.
- Tasks: 2; production/test/config files: 50.
- Actual token estimate: ceiling of realized production/test/config Git diff characters divided by four, not model/harness usage; metadata summary excluded from that diff.

## Accomplishments and Verification

- First-Admin bootstrap serializes on singleton guard, never overwrites an existing Admin. Immutable normalized username, role and digest constraints live in the real PostgreSQL schema; vector extension version verified as 0.8.7.
- Auth routes expose safe DTOs and no-store responses. JSON/custom header and exact Origin/Host protect login; synchronizer CSRF protects authenticated mutations. Cookies are host-only, HttpOnly, Strict and Secure=false only under validated loopback HTTP configuration. No localStorage authentication or OpenAI calls.
- Dataset query filters technician grants before count and pagination; initial empty lists come from PostgreSQL. Admin accounts page displays the real authenticated account; full account mutations belong to Plan 02.
- GET polling does not renew idle time. Visible navigation and trusted key/pointer events send throttled activity without timer heartbeats. Resolver rejects equality at 30 minutes idle or 8 hours absolute. Row-locked logout/activity plus conditional update prevent stale activity from reviving committed revocation. Already-authorized responses cannot be recalled.
- `docker compose run --rm frontend-test npm run test:e2e -- phase1.spec.ts --grep tracer`: **1 passed, 1.5s** final run (browser scenario 800ms). Repeated after Task 1 commit before expansion: **1 passed, 1.4s**.
- Exact Task 2 command against built backend-test image: **17 passed, 5.59s**. Full backend `python -m pytest -q`: **17 passed, 5.51s**. No skipped tests and no zero-test suites.
- `npm run typecheck` and `npm run lint` in next-test production image passed. Final Next production build completed in 7.2s with TypeScript checks and all four pages generated. Hash-locked Python install and `pip check` passed; npm lock/ci audit reports **0 vulnerabilities**.
- Same Alembic revision upgrades empty isolated DB, preserves rows on repeat, and API readiness returns 503 before head. Concurrent bootstrap yields exactly one first Admin. Mutation failures roll back request-scoped sessions.
- Browser fixture created one dataset/session visible to both api-test and backend-test. Independently queried operational PostgreSQL: **0 Browser WMS rows and 0 sessions**. Test services have a separate internal network/volume and no host ports; production publishes frontend only at 127.0.0.1:3000. Actual host socket/persistence acceptance remains Plan 05.

## Task Commits

1. Task 01-01-01: `5c05bf8` — authenticated browser/PostgreSQL tracer.
2. Task 01-01-02 RED: `a452813` — behavioral failure evidence, 7 failed / 6 passed before implementation; missing timeout rejection and activity endpoint, no syntax/import failure.
3. Task 01-01-02 GREEN: `fcf769d` — expiry, conditional activity, frontend integration and stale-snapshot regression test.
4. Summary metadata: separate docs commit after self-check.

## Deviations from Plan

- **[Rule 1 — Dependency compatibility/security]** Research pins were candidates. TypeScript 7.0.2 exceeded official typescript-eslint peer range; selected 6.0.3. Next lint preset introduced five high audit findings through unpatched braces (GHSA-vfj7-8cjw-p6xm); omitted that optional preset and used official typescript-eslint rules. Final audit zero. Included in `5c05bf8`.
- **[Rule 1 — Proxy behavior]** First real browser tracer failed 403 because Next rewrites changed Host to api-test:8000. Allowed only the exact configured internal destination or browser Host while retaining exact browser Origin and rejecting arbitrary forwarded headers. Real browser subsequently passed. Included in `5c05bf8`.
- **[Rule 3 — Test plumbing]** Added `backend/tests/support.py`, package initializer and ESLint config for isolated fixtures and lint. Tests require the validated rag_test target; production registers no fixture routes. Disabled pytest's read-only cache and TypeScript incremental writes in nonroot check commands. Included in `5c05bf8`.
- **[Rule 2 — Hook integration]** Task 2 also updates workspace layout and local-development documentation to actually connect the planned hook and explain session semantics. Included in `fcf769d`.

## Issues Encountered

Initial October 4 Playwright extraction exhausted C: and made Docker storage read-only. Execution stopped before commits or runtime claims. User freed space; orchestrator recovered Docker. Resumed successfully October 5 without relocation or pruning. All later builds reused pinned base images; final available C: space was approximately 1.3 GB. Continue monitoring storage before later builds.

One existing library compatibility warning remains: Starlette deprecates its working httpx-backed TestClient path. Tests pass with the locked FastAPI/httpx stack; no speculative httpx2 install performed. ESLint 9 emits upstream support deprecation during install; lint and audit pass. No stub, skipped test or unrun task verification remains.

## Threat Flags

| Flag | File | Description |
|------|------|-------------|
| threat_flag: test-only endpoints | backend/tests/support.py | Reset/proof endpoints exist only in validated isolated TEST_MODE, no production registration, no test host ports, and no access to operational network. Never enable this mode for operational data. |

## Next Plan Readiness

Shared contracts: Account/Session/DatasetPage DTOs, `get_db`, `get_identity`, `get_account`, `unsafe_identity`, `require_admin`, `dataset_query`, `SessionLocal`, Account/AuthSession/Dataset/DatasetGrant/AdminGuard/LoginRateBucket models. Auth routes: `/api/v1/auth/login`, `/session`, `/logout`, `/activity`; dataset list `/api/v1/datasets`. Request-scoped dependency owns rollback; mutating service/route owns explicit commit.

Tests import PASSWORD and HEADERS from `tests.conftest`, use isolated `db`, `client`, `admin` fixtures, and injected `sessions.now_utc`. Run suites sequentially: reset shares rag_test; never reset operational DB. `tests.support` mounts only in test mode. Frontend `api()` dispatches session-expired on 401; workspace clears protected children and redirects login.

Plan 02 owns account mutations, forced password change/rotation and bounded login limiter; schema is prepared without exposing those unfinished endpoints. Plan 03 owns dataset metadata mutations/grants/detail. Plan 04 owns safe system status/demo seed/module contracts. Plan 05 owns full browser acceptance, operational restart/socket/persistence smoke. No ingestion, RAG, provider, agent or report endpoint was added.

Actual local `.env` was generated with a random database secret, contains no OpenAI key and is Git ignored. Operational PostgreSQL was migrated but no real Admin credential was silently created; documented getpass bootstrap remains the operator's initial-account step. STATE/ROADMAP/REQUIREMENTS changes belong to the orchestrator and were deliberately not touched by this executor.

## Self-Check: PASSED

All 50 changed production/test/config artifacts exist; Task 1, RED and GREEN commits resolve in Git. Summary claims match recorded passing test/build output; no task verification was skipped.

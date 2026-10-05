---
phase: 01-local-workspace-and-access-control
plan: "02"
subsystem: auth
tags: [admin, accounts, csrf, password-recovery, postgres, rate-limit, playwright]
requires:
  - phase: 01-01
    provides: "Migrated identity/session schema, same-origin auth and isolated runtime tests"
provides:
  - "Admin account creation, metadata/role/active changes and password reset through right dialog"
  - "Transactional last-Admin protection and target-session revocation with safe audit records"
  - "Mandatory temporary-password change, session/CSRF rotation preserving absolute deadline"
  - "Bounded per-username/actual-peer rolling five-minute login-failure limiter"
affects: [01-03, 01-04, 01-05, authorization]
tech-stack:
  added: []
  patterns: [admin guard before actor-session resolution, timestamped rolling failure rows, native accessible modal dialog, forced password route before workspace]
key-files:
  created: [backend/app/auth/accounts.py, backend/app/api/users.py, backend/app/auth/rate_limit.py, backend/tests/integration/test_admin_users.py, frontend/src/components/AccountPanel.tsx, frontend/src/app/change-password/page.tsx, frontend/tests/e2e/accounts.spec.ts]
  modified: [backend/app/main.py, backend/app/api/schemas.py, backend/app/api/auth.py, backend/app/api/dependencies.py, backend/tests/integration/test_auth.py, frontend/src/app/login/page.tsx, frontend/src/app/(workspace)/layout.tsx, frontend/src/hooks/use-session.ts, frontend/src/app/(workspace)/accounts/page.tsx]
key-decisions:
  - "Acquire administration guard before resolving actor session on account mutations; avoid cross-Admin session-row/guard deadlocks and recheck current principal after waiting."
  - "Represent each failed login as timestamped username and peer digest rows in existing bucket table; serialize count/write with separate PostgreSQL advisory transaction lock for true rolling semantics."
  - "Password changes use the same administration guard, revoke every old account session, then create a new token/CSRF with original created_at."
  - "Native dialog provides right-panel modal focus containment; secret fields are cleared on error, save and dismissal."
requirements-completed: [AUTH-01, AUTH-02, SYS-04]
coverage:
  - id: D1
    description: "Admin user mutations, technician denial, normalized duplicate conflict, self/last-Admin protection, concurrent updates and rollback"
    requirement: AUTH-02
    verification:
      - {kind: integration, ref: "backend/tests/integration/test_admin_users.py", status: pass}
    human_judgment: false
  - id: D2
    description: "Temporary password recovery, cookie/CSRF rotation, reset and disable invalidating second browser"
    requirement: AUTH-01
    verification:
      - {kind: e2e, ref: "frontend/tests/e2e/accounts.spec.ts", status: pass}
      - {kind: integration, ref: "backend/tests/integration/test_auth.py#test_forced_password_rotation_preserves_absolute_deadline", status: pass}
    human_judgment: false
  - id: D3
    description: "Rolling rate-limit recovery, spoofed forwarded IP rejection, simultaneous failures and bounded storage"
    requirement: AUTH-01
    verification:
      - {kind: integration, ref: "backend/tests/integration/test_auth.py", status: pass}
    human_judgment: false
actuals:
  tokens: 10363
  tasks: 2
  commits: 5
duration: 27min
completed: 2026-10-05
status: complete
---

# Phase 1 Plan 02: Account administration and password recovery Summary

**Admin account management with a Vietnamese right dialog, serialized last-Admin protection, mandatory temporary-password recovery and bounded rolling login limits.**

## Performance and Verification

- Execution approximately 2026-10-05 07:14–07:41 UTC, 27 minutes; 2 tasks, 16 production/test files.
- Actual tokens are realized production/test Git diff characters divided by four, rounded up; no harness usage or summary metadata mixed into this scale.
- Task 1 exact built-image command `docker compose run --rm backend-test python -m pytest tests/integration/test_admin_users.py -q`: **4 passed, 2.82s**. Final full suite also includes additional disable/audit assertions.
- Task 2 exact command `docker compose run --rm frontend-test npm run test:e2e -- accounts.spec.ts`: **1 passed, 3.7s** (browser scenario 3.0s).
- Final full backend `docker compose run --rm backend-test python -m pytest -q`: **26 passed, 11.13s**, including actual PostgreSQL independent-connection races, rolling-window and storage-bound checks.
- Original real-browser tracer regression: **1 passed, 2.4s**. Final Next production build passed with TypeScript and `/change-password` generated; separate next-test `npm run typecheck` and `npm run lint` passed.
- No skipped tests, empty suites, unrun task verification or real AI calls. Existing Starlette/httpx TestClient deprecation warning remains; no dependency changes or speculative replacements.

## Accomplishments

- Admin-only GET/POST `/api/v1/admin/users`, PATCH `/{id}` and POST `/{id}/reset-password` call account services. Creation normalizes immutable usernames, rejects duplicates with 409, validates allowlisted DTOs and marks every new account for password change. Metadata-only idempotent edits preserve sessions; role changes, disable and reset revoke target sessions in the same commit.
- Bootstrap and account mutations share the singleton administration guard. Self-disable/self-demotion and removal of the last active Admin are rejected. Independent PostgreSQL connections/barrier prove simultaneous cross-Admin changes leave one active Admin. Injected commit failure rolls back password and session revocation together. Audit records contain actor/action/object IDs only; test snapshots exclude both original and temporary passwords.
- Account table is paginated and refreshes only after committed save. Right-side native dialog has labelled inputs, default username focus, modal focus containment, Escape/close, retained nonsensitive validation state and cleared password fields.
- Forced users retain session/CSRF/change/logout access but cannot use protected dataset/Admin APIs. Login and direct workspace entry redirect to `/change-password`. Correct current password and distinct 15–128-character new password are required. Rotation revokes every old session and changes token/CSRF without extending original eight-hour creation deadline.
- Real browser creates a technician through the dialog, changes their temporary password, confirms old cookie and old CSRF rejection, and then observes reset and disable invalidating a second browser on its next request. New cookie accesses the real dataset workspace; UI clears stale protected state on 401.
- Five failures for username or actual transport peer in a rolling five-minute window yield 429 with Retry-After. Unknown usernames still perform dummy Argon2 verification; failures remain generic. Arbitrary X-Forwarded-For does not influence peer identity. Timestamped failure rows expire individually; independent concurrent attempts cannot lose counts; storage is capped at 10,000 rows with safe retry after expiry and no permanent account lockout.

## Task Commits and TDD Gates

1. Task 01-02-01 RED: `e72fca3` — 4 behavioral failures from missing account routes, including the concurrent Admin test.
2. Task 01-02-01 GREEN: `36015f0` — account API/service/dialog and passing PostgreSQL tests.
3. Task 01-02-02 RED: `7b565b1` — 2 behavioral failures (missing password-change route and absent 429 limiter), 7 existing auth cases passing.
4. Task 01-02-02 GREEN: `c8a88b7` — recovery, limiter, routing, final race/rolling/audit/browser coverage.
5. Separate summary metadata commit follows self-check.

Both tasks followed RED→GREEN; failures were observable missing behavior rather than import or syntax errors. No refactor commit was necessary.

## Decisions and Deviations

- **[Rule 2 — Correct lock ordering]** Account mutations acquire guard before actor-session resolution. Using the generic unsafe session-row lock first would let two Admins each hold their own session while attempting to revoke the other; current principal is re-read after guard wait. Password change uses matching order. This is an implementation detail of the planned concurrency invariant, with no schema/infrastructure change.
- **[Rule 2 — Connect forced workflow]** Task 2 also modifies central dependencies, login page and workspace layout to enforce `password_change_required` and route forced users before protected children render. A standalone change page/hook could not meet D-03 without those integration points. Adds no scope.
- Rate limiting reuses the already migrated LoginRateBucket schema, using individual failure timestamps and a dedicated transaction advisory lock; no new table, service or package.

## Issues, Stubs and Threat Review

No execution blocker or unresolved stub. Docker storage recovery/relocation was completed by the orchestrator before this plan; images and both database volumes were preserved. All builds reused pinned dependency layers. No new security surface beyond the planned account/password/login boundaries. Existing test-only helper routes remain confined to the isolated test topology.

AUTH-02's planning classifier edge row remains **unclassified**; these concrete validation/race tests do not claim to resolve that separate classification flag. Audit logs are safe process records, not a new durable audit database. Already-authorized responses cannot be recalled after a later revocation; subsequent authentication uses current state.

## Next Plan Readiness

Account service exposes `lock_manager`, `create_account`, `update_account`, `reset_password`, `revoke_sessions` and `record_audit`. User router `manager` and `mutation_manager` provide unrestricted current Admin enforcement; later grant mutations should retain guard/current-principal ordering when interacting with session revocation. `get_account` returns 403 `password_change_required` for forced users, covering future business/status routes using that dependency.

Authentication routes now include `/api/v1/auth/change-password`, with current/new password fields and safe SessionDTO response. `sessionDestination` in the session hook centralizes forced/Admin/technician landing. AccountPanel renders create/edit/reset; no account hard-delete endpoint exists. Future Plan 03 owns grant panels/dataset edits, Plan 04 status/demo/contracts, Plan 05 full acceptance.

STATE/ROADMAP/REQUIREMENTS/config remain orchestrator-owned and were not modified by this executor. Unrelated `docs/host-docker-storage.md` and runtime `.gsd/` preserved.

## Self-Check: PASSED

All 16 changed production/test files exist. Both RED and both GREEN commits resolve in Git. Verification above reflects final built-image runtime output; no mandatory check omitted.

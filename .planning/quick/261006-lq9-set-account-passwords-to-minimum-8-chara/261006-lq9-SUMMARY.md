---
quick_id: 261006-lq9
type: quick
subsystem: auth
tags: [password-policy, FastAPI, Next.js, Playwright]
status: complete
requires: []
provides:
  - Consistent inclusive 8–128 character account-password policy across API, CLI, and browser flows.
  - Backend and browser boundary coverage for short account passwords.
affects: [authentication, account-management, local-development]
tech-stack:
  added: []
  patterns: [One shared account-password boundary across request schemas and password hashing validation.]
key-files:
  created: []
  modified:
    - backend/app/auth/passwords.py
    - backend/app/api/schemas.py
    - backend/app/api/auth.py
    - backend/scripts/bootstrap_admin.py
    - backend/scripts/seed_demo.py
    - backend/tests/integration/test_auth.py
    - backend/tests/integration/test_admin_users.py
    - backend/tests/integration/test_bootstrap_seed.py
    - frontend/src/app/login/page.tsx
    - frontend/src/app/change-password/page.tsx
    - frontend/src/components/AccountPanel.tsx
    - frontend/tests/e2e/accounts.spec.ts
    - docs/local-development.md
key-decisions:
  - "Count the original password string as supplied; add no trimming or composition rules."
  - "Keep the PostgreSQL .env secret requirement separate from the account-password policy."
requirements-completed: []
coverage:
  - id: D1
    description: Account passwords accept 8–128 characters across backend API, CLI, and browser account flows, with boundary checks at 7, 8, 128, and 129.
    verification:
      - kind: integration
        ref: "docker compose run --rm backend-test python -m pytest -q tests/integration/test_auth.py tests/integration/test_admin_users.py (16 passed)"
        status: pass
      - kind: integration
        ref: "docker compose run --rm backend-test python -m pytest -q tests/integration/test_bootstrap_seed.py (12 passed)"
        status: pass
      - kind: e2e
        ref: "frontend/tests/e2e/accounts.spec.ts (4 passed)"
        status: pass
    human_judgment: false
duration: 9min
completed: 2026-10-06
---

# Quick Task 261006-lq9 Summary

**Account passwords now accept 8–128 characters across authentication, account administration, bootstrap, seed, and browser flows.**

## Performance

- **Duration:** 9 minutes
- **Started:** 2026-10-06T08:45:27Z
- **Completed:** 2026-10-06T08:53:49Z
- **Tasks:** 3
- **Files modified:** 13

## Accomplishments

- Lowered the shared backend password validator and all request-schema constraints to 8 characters while preserving the 128-character maximum and returning the password unchanged.
- Updated bootstrap and demo-seed prompts, login/change/account-panel fields, and local-development guidance to state the 8–128 account-password policy.
- Added backend policy-boundary checks and API/CLI lifecycle coverage; browser coverage proves an 8-character temporary password works for login and password change and that 7 characters fail HTML validity checks.

## Files Created/Modified

- `backend/app/auth/passwords.py`, `backend/app/api/schemas.py`, `backend/app/api/auth.py` — shared and request-level password limits.
- `backend/scripts/bootstrap_admin.py`, `backend/scripts/seed_demo.py` — CLI policy prompts.
- `backend/tests/integration/test_auth.py`, `backend/tests/integration/test_admin_users.py`, `backend/tests/integration/test_bootstrap_seed.py` — 7/8 and 128/129 boundaries and password lifecycle.
- `frontend/src/app/login/page.tsx`, `frontend/src/app/change-password/page.tsx`, `frontend/src/components/AccountPanel.tsx` — browser constraints and user guidance.
- `frontend/tests/e2e/accounts.spec.ts` — 8-character account lifecycle and short-input validity checks.
- `docs/local-development.md` — account-password guidance, explicitly separate from the PostgreSQL `.env` secret.

## Decisions Made

- Followed the requested 8–128 account-password policy, with no trimming or composition rules.
- Preserved Argon2 hashing, session rotation and deadlines, CSRF checks, and login rate limiting.
- Kept the database `POSTGRES_PASSWORD` requirement unchanged and separate from account passwords.

## Deviations from Plan

None — the plan was executed as written.

## Issues Encountered

- `docker` was not on the shell PATH; the installed Docker CLI was invoked by its absolute path. All requested checks completed successfully.
- Backend checks emitted the existing Starlette `TestClient` deprecation warning; it did not affect the results.

## Verification Results

- Auth and admin integration tests: **16 passed**.
- Bootstrap and seed integration tests: **12 passed**.
- Accounts browser E2E: **4 passed**.
- `.env` remained unchanged; no operational PostgreSQL resources were used.

## Commit Handling

No commit was created in this delegated execution; the parent executor owns Git staging and commits.

## Self-Check: PASSED

- Summary file exists at the quick-task path.
- All three plan-scoped verification commands passed.
- Commit verification is deferred to the parent executor, which owns commits for this shared task.

---
*Quick task: 261006-lq9*
*Completed: 2026-10-06*

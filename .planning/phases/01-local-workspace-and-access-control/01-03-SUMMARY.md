---
phase: 01-local-workspace-and-access-control
plan: "03"
subsystem: auth
tags: [datasets, acl, postgresql, csrf, concurrency, playwright, nextjs]
requires:
  - phase: 01-01
    provides: "Migrated datasets/grants, opaque sessions and isolated PostgreSQL/browser tests"
  - phase: 01-02
    provides: "Current identity, shared administration guard, account services and Vietnamese right dialogs"
provides:
  - "Admin dataset metadata creation/editing and technician grant-filtered list/detail/count"
  - "Fresh database principal/grant recheck before dataset content responses"
  - "Idempotent per-pair grant/revoke, technician-only targets and safe audit identifiers"
  - "Vietnamese grant dialog, partial-save reconciliation and passive live technician scope refresh"
affects: [01-04, 01-05, ingestion, retrieval, source-access, history, reports]
tech-stack:
  added: []
  patterns: [current database capability policy, captured scope before count/page, final response scope recheck, per-pair PostgreSQL upsert/delete, passive scope reconciliation]
key-files:
  created: [backend/app/database/datasets.py, backend/tests/integration/test_acl.py, frontend/src/components/DatasetGrantPanel.tsx, frontend/tests/e2e/datasets.spec.ts]
  modified: [backend/app/api/datasets.py, backend/app/api/schemas.py, backend/app/api/users.py, backend/app/auth/policy.py, frontend/src/app/(workspace)/datasets/page.tsx, frontend/src/hooks/use-session.ts, frontend/src/lib/api.ts, frontend/src/lib/contracts.ts]
key-decisions:
  - "Capture current allowed IDs and constrain the SQL count/page query to that scope, then run fresh current-principal/grant SQL before responding; a revoked detail matches the missing-resource 404 and a revoked list returns no items/count."
  - "Reuse the existing administration guard before identity/CSRF resolution for grant mutations; serialize each pair transaction with account role changes instead of introducing another lock or full-set grant writes."
  - "Load committed grants after every save attempt, including partial failure; five-second/focus/visibility GET refreshes clear revoked details without renewing session activity."
  - "Delegate remaining Git staging/commits to the orchestrator after child approval calls were aborted; preserve atomic RED/GREEN commits and keep shared state documents owned by the root."
requirements-completed: [AUTH-03, AUTH-04, AUTH-05, SYS-04]
coverage:
  - id: D1
    description: "Admin metadata persistence, validation/rollback and current grant-filtered technician list/detail/count with final-response revocation rejection"
    requirement: AUTH-04
    verification:
      - {kind: integration, ref: "backend/tests/integration/test_acl.py#test_metadata_admin_validation_and_rollback", status: pass}
      - {kind: integration, ref: "backend/tests/integration/test_acl.py#test_current_acl_count_detail_and_zero_default", status: pass}
      - {kind: integration, ref: "backend/tests/integration/test_acl.py#test_revoke_after_lookup_before_response", status: pass}
    human_judgment: false
  - id: D2
    description: "Admin per-item grants, current-session scope change, safe targets, rollback and concurrent duplicate/opposing writes"
    requirement: AUTH-03
    verification:
      - {kind: integration, ref: "backend/tests/integration/test_acl.py#test_grants_idempotent_safe_targets_live_session_and_rollback", status: pass}
      - {kind: integration, ref: "backend/tests/integration/test_acl.py#test_independent_connection_grant_races", status: pass}
      - {kind: integration, ref: "backend/tests/integration/test_acl.py#test_opposing_grants_follow_serialized_commit_order", status: pass}
    human_judgment: false
  - id: D3
    description: "Two-browser Vietnamese dataset workflow, zero-grant guidance, open-page revocation clearing, partial-save authoritative refresh and modal focus return"
    requirement: SYS-04
    verification:
      - {kind: e2e, ref: "frontend/tests/e2e/datasets.spec.ts", status: pass}
    human_judgment: false
actuals:
  tokens: 9543
  tasks: 2
  commits: 5
duration: 157min
completed: 2026-10-05
status: complete
---

# Phase 1 Plan 03: Dataset metadata and live grants Summary

**Admin dataset metadata and per-item grants with PostgreSQL current-scope enforcement, final-response revocation checks and a Vietnamese workspace that clears revoked content.**

## Performance and Verification

- Execution window approximately 2026-10-05 07:43–10:20 UTC: 157 minutes wall time, including interrupted child Git approvals and waiting for orchestrator commits; this is not an active coding-time measurement.
- Two tasks, 12 production/test files. Actual tokens are `ceil(38171 / 4) = 9543` over the realized UTF-8-decoded Git diff `380b300..91947f2 -- backend frontend`; no harness tokens or planning metadata mixed into the estimate scale.
- Task 1 built-image ACL command: **3 passed, 2.58s**. Task 1 Next production build and TypeScript completed successfully.
- Final exact ACL command `docker compose run --rm backend-test python -m pytest tests/integration/test_acl.py -q`: **7 passed, 6.06s**.
- Final full backend `docker compose run --rm backend-test python -m pytest -q`: **33 passed, 15.90s**, using migrated `postgres-test/rag_test` and independent connections for race cases.
- Exact Task 2 browser command `docker compose run --rm frontend-test npm run test:e2e -- datasets.spec.ts`: **1 passed, 14.1s** (scenario 13.4s).
- Final full browser regression `docker compose run --rm frontend-test npm run test:e2e`: **3 passed, 16.6s**; account recovery 3.1s, dataset workflow 12.0s and original authentication tracer 789ms.
- Final Next production build passed with TypeScript and all workspace routes generated. Separate `npm run typecheck` and `npm run lint` in the next-test image passed.
- No skipped tests, empty suites, unrun task verification or real AI calls. The existing Starlette/httpx TestClient deprecation warning remains unchanged. No dependencies, image pins, migrations or operational fixture data were changed.

## Accomplishments

- Admin POST `/api/v1/admin/datasets` and PATCH `/{id}` persist bounded metadata: names 1–128 and descriptions 0–2000 Unicode characters; UUID paths, allowlisted DTOs, safe duplicate-name conflicts and transaction rollback. The dataset workspace creates/edits metadata in a right dialog and reads real detail responses.
- Technician queries filter grants before total/count/pagination, with positive page, page size 1–100 and deterministic `created_at/id` ordering. New technicians receive zero grants. Hidden and unknown dataset IDs return the same 404 JSON. A separate connection can revoke grants after lookup; fresh SQL before response prevents detail content or list rows/count from escaping that revoked scope.
- Capability helpers live outside RAG, deny unknown roles and resolve principals/grants from PostgreSQL. Admin repository management capabilities remain distinct from technician analysis/ticket-input/report capabilities. Future modules must call these policies; their endpoints are not implemented by this plan.
- GET `/api/v1/admin/users/{id}/datasets` and PUT/DELETE `/{dataset_id}` target existing technicians. The existing primary-key pair and PostgreSQL conflict-safe insert prevent duplicate grants. Each transaction changes only one pair, preserves other datasets and serializes with role changes via the existing administration guard. Mutations require current Admin identity and CSRF; audits contain actor/action/account/dataset identifiers only.
- The grant dialog loads committed state across all account/dataset pages, applies per-item differences and refreshes server state after success or partial failure. It never labels a partial save as successful. Native modal focus is restored explicitly on dismissal.
- An already-open technician page observes grants/revocations through passive five-second and focus/visibility GET refreshes. Rejections clear selections/details/panels; request sequence checks prevent stale asynchronous responses from repopulating cleared state. Passive reads do not call the activity endpoint or extend idle expiry.

## Task Commits

1. Task 01-03-01 RED: `4894682` — failing metadata/current-ACL tests; initial run 3 failed in 2.51s against missing endpoints/service.
2. Task 01-03-01 GREEN: `b905b19` — metadata APIs, bounded DTOs, shared current policy, final-response checks and dataset UI.
3. Task 01-03-02 RED: `c238f6c` — per-item grant/race and browser checks; 2 failed / 3 passed in 3.84s against missing grant endpoints.
4. Task 01-03-02 GREEN: `91947f2` — per-pair grants, safe audits, committed-state dialog, live-scope refresh and complete race/browser assertions.
5. SUMMARY metadata: separate orchestrator docs commit after self-check, before shared STATE/ROADMAP updates.

Both tasks have a RED commit before their corresponding GREEN commit. There are no intentional or unexpected tracked-file deletions.

## Decisions Made

- List responses capture the permitted ID set and use it in the count/page SQL before a fresh final scope check. This also prevents a newly granted, subsequently revoked dataset entering a response whose initial scope did not contain it.
- Grant mutations reuse the existing administration guard and current-session/CSRF helpers. Each request writes one pair; no bulk replacement, new table, auth scheme or infrastructure was needed.
- Permission changes reconcile through passive GETs, independently of trusted user activity used for the session idle timer.

The fresh ORM principal reload and pair UPSERT follow the pinned [SQLAlchemy 2.0 populate-existing documentation](https://docs.sqlalchemy.org/en/20/orm/queryguide/api.html#populate-existing) and [PostgreSQL conflict handling documentation](https://docs.sqlalchemy.org/en/20/dialects/postgresql.html#insert-on-conflict-upsert).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 — Bug] Restore focus after closing the grant dialog**
- Found during Task 2 browser verification: the grant/revoke workflow passed, but the final opener-focus assertion failed.
- Fixed explicit opener capture/restoration in dialog cleanup.
- File: `frontend/src/components/DatasetGrantPanel.tsx`; commit `91947f2`.
- Verified by the final focused and full browser runs.

**2. [Rule 1 — Test harness] Synchronize commit-order barriers inside the FastAPI worker thread**
- Found during the first full backend run: 31 passed / 2 failed in 57.23s. The new controlled-order tests set a thread-local flag in the TestClient caller thread, so the handler's worker never signaled the barrier.
- Moved the flag setup into the patched dataset service running on the handler thread; production grant code was unchanged.
- File: `backend/tests/integration/test_acl.py`; commit `91947f2`.
- Verified both PUT→DELETE and DELETE→PUT final states; final ACL 7/7 and full backend 33/33 passed.

### Execution Coordination

- Child Git escalation calls were interrupted/aborted, including one after 415.1s and another after 626s. Read-only checks found no index lock or task Git process, only fsmonitor daemons. The orchestrator centrally committed Task 2 RED/GREEN and will commit this SUMMARY. Atomic task boundaries were preserved; this executor did not modify shared STATE, ROADMAP, REQUIREMENTS, config or handoff files.

## Scope and Remaining Obligations

- AUTH-03/04/05 unclassified edge rows remain flagged as specified in the plan. Passing metadata/grant tests do not resolve those unspecified assumptions or prove future source/retrieval/history/report/PDF endpoints.
- Composite report authorization, provenance/module contracts and seed/status work continue in Plan 04; host binding/persistence and final usability acceptance continue in Plan 05.
- No ingestion, documents, dataset deletion, RAG, report output, scheduler, OCR, Agent tools or AI provider calls were added. No known stubs or open defects were introduced in this implemented slice.
- No user setup or authentication gate was needed. Root-owned untracked `docs/host-docker-storage.md` and other concurrent planning changes were preserved.

## Next Phase Readiness

Current dataset metadata/grants and reusable policy helpers are available for Plan 04. The dataset UI and existing authentication/account workflows pass against the isolated local API/PostgreSQL stack. Shared planning state advancement belongs to the orchestrator after this SUMMARY is committed.

## Self-Check: PASSED

- All four newly created production/test artifacts and this SUMMARY exist on disk.
- Commits `4894682`, `b905b19`, `c238f6c` and `91947f2` exist as Git commit objects.
- The realized diff contains the 12 declared source/test files and no tracked-file deletions.
- No skipped tests, TODO/FIXME stubs or unrun task verification remain in this slice.

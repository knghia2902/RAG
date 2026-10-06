---
phase: 01-local-workspace-and-access-control
plan: "04"
subsystem: auth
tags: [authorization, pydantic, protocols, postgresql, seed, configuration, nextjs, playwright]
requires:
  - phase: 01-03
    provides: "Current SQL account/grant policy, dataset metadata services, shared administration guard and isolated runtime tests"
provides:
  - "Pure whole-resource authorization with current SQL snapshots and generic revoked-scope denial"
  - "Immutable bounded source/scope/index/evidence DTOs and independent parser/embedding/retrieval/generation protocols"
  - "Separate transactional replay-safe demo seed with new-account-only initial grants"
  - "Provider-free health/readiness and Admin-only safe configuration status with Vietnamese Web navigation"
affects: [01-05, ingestion, retrieval, ticket-analysis, source-access, history, reports, provider-adapters]
tech-stack:
  added: []
  patterns: [immutable backend principal snapshot, pure all-provenance policy, current SQL final recheck, provider-free protocol boundaries, shared guard insert-only seed, boolean status DTO allowlist]
key-files:
  created: [backend/app/rag/contracts.py, backend/app/llm/contracts.py, backend/scripts/seed_demo.py, backend/app/api/status.py, backend/app/api/health.py, backend/tests/unit/test_policy.py, backend/tests/unit/test_module_boundaries.py, backend/tests/integration/test_bootstrap_seed.py, backend/tests/integration/test_startup.py, frontend/src/app/(workspace)/configuration/page.tsx, frontend/src/components/Sidebar.tsx, frontend/tests/e2e/status.spec.ts, docs/module-boundaries.md, docs/security-contracts.md]
  modified: [backend/app/auth/policy.py, backend/app/main.py, frontend/src/app/(workspace)/layout.tsx]
key-decisions:
  - "Separate pure require_all_datasets from current_principal/authorize_resource SQL refresh; authority snapshots are backend-only and future consumers must refresh before returning content/files."
  - "Admin report-read is global; scoped roles require complete nonempty provenance, and permission_changed never discloses revoked identifiers."
  - "Seed uses the existing singleton administration guard and one transaction; initial grant is created only with a newly inserted demo-granted account, so replay cannot undo revocation."
  - "Configuration exposes only database_ready/provider_configured; configured means key presence, with no provider connection check or API-key editing."
requirements-completed: [AUTH-04, AUTH-05, SYS-01, SYS-04]
coverage:
  - id: D1
    description: "A+B whole-resource denial after A revoke, B-only allowance, current SQL refresh, disabled Admin/default deny and explicit scoped capability extension"
    requirement: AUTH-04
    verification:
      - {kind: unit, ref: "backend/tests/unit/test_policy.py", status: pass}
    human_judgment: false
  - id: D2
    description: "Provider-free module imports and immutable bounded locator/model/index/scope/query/evidence/generation DTO round-trips"
    requirement: SYS-04
    verification:
      - {kind: unit, ref: "backend/tests/unit/test_module_boundaries.py", status: pass}
    human_judgment: false
  - id: D3
    description: "Separate seed requires Admin and preserves edits/revoked grants on replay/concurrency with complete rollback before commit"
    requirement: SYS-01
    verification:
      - {kind: integration, ref: "backend/tests/integration/test_bootstrap_seed.py", status: pass}
    human_judgment: false
  - id: D4
    description: "No-key startup, boolean-only protected status, secret-safe readiness, passive expiry and Vietnamese Admin configuration/error/retry/technician denial"
    requirement: SYS-04
    verification:
      - {kind: integration, ref: "backend/tests/integration/test_startup.py", status: pass}
      - {kind: e2e, ref: "frontend/tests/e2e/status.spec.ts", status: pass}
    human_judgment: false
actuals:
  tokens: 13199
  tasks: 2
  commits: 5
duration: 27min
completed: 2026-10-06
status: complete
---

# Phase 1 Plan 04: Authorization contracts and safe local operations Summary

**Whole-provenance current authorization, replaceable provider-free DTO/protocol contracts, transactional insert-only demo seeding and an Admin-only Vietnamese configuration status page.**

## Performance and Verification

- Execution approximately 2026-10-06 00:58–01:25 UTC: 27 minutes wall time, including central Git approval/commit waits. Two tasks, 25 production/test/documentation/directory-marker files.
- Actual tokens: `ceil(52796 / 4) = 13199` over the UTF-8-decoded realized Git diff `cf969df..efb3b75 -- backend frontend docs/module-boundaries.md docs/security-contracts.md data storage`. This includes shipped documentation and marker diffs, excludes planning metadata, and does not use harness tokens. Commit count includes four task commits and the separate root-owned SUMMARY metadata commit.
- Final exact Task 1 command `docker compose run --rm backend-test python -m pytest tests/unit/test_policy.py tests/unit/test_module_boundaries.py -q`: **25 passed, 3.57s**.
- Final exact Task 2 command `docker compose run --rm backend-test python -m pytest tests/integration/test_bootstrap_seed.py tests/integration/test_startup.py -q`: **14 passed, 7.52s**. That image contains the final seed/startup code and tests; subsequent backend rebuild only expanded explicit Admin policy test parameters.
- Final rebuilt-image full backend `docker compose run --rm backend-test python -m pytest -q`: **72 passed, 33.35s**, on isolated migrated `postgres-test/rag_test`, followed sequentially by browser verification.
- Final full browser `docker compose run --rm frontend-test npm run test:e2e`: **4 passed, 18.8s**. Configuration scenario 1.9s; account recovery 2.9s, dataset grants/revoke 12.2s and login tracer 856ms.
- Production Next build passed, compiling in 3.4s and completing TypeScript in 2.6s, with `/configuration` generated. Separate `next-test npm run lint` and `npm run typecheck` both passed. No dependency, lockfile, image pin, migration, operational account/data or provider-call changes.
- Existing Starlette/httpx TestClient deprecation warning is unchanged. No skipped tests, zero-test suites or unrun task verification remains.

## Accomplishments

- `Principal` is an immutable internal snapshot. `current_principal` reloads account state and current grants; `authorize_resource` calls pure `require_all_datasets`. A scoped A+B resource is wholly denied after A revoke with generic `permission_changed`; B-only passes. Missing technician provenance denies. Active Admin report-read passes globally, including empty legacy provenance; disabled/forced-change Admin and unknown roles deny. Explicit scoped capability mapping permits future role extension without importing policy into RAG. Technician ticket analysis remains separate from repository upload/delete/reindex.
- RAG and LLM contracts import without settings, API keys or provider clients. Parser/Chunker/EmbeddingProvider/Retriever and distinct LLMProvider are protocols, with importable business ownership packages and no fake business implementations. Immutable allowlisted DTOs preserve source UUID/version/optional locator and embedding model/dimension/index UUID through JSON. Tests cover inclusive min/max and one step outside for locator positions/text, dataset counts, dimension/model metadata, queries, evidence, generation questions/text and selected evidence/citation counts. RAG receives authorized scope rather than role identity.
- Documentation records caller authority, DTO/OpenAPI/frontend synchronization, adapter replacement, selected-evidence/provider redaction/limits and canonical database metrics. Future source/download/lifecycle, every retrieval/context/history branch, ticket input and report/history/PDF/file-serving endpoints have explicit direct unauthorized/revoked API acceptance obligations. Those endpoints are not implemented or claimed verified here.
- `python -m scripts.seed_demo` is separate from first-Admin bootstrap and prompts through getpass for the two technicians' passwords. An active Admin is required. The shared administration guard serializes complete metadata/account/grant transactions, including concurrent service invocations. Existing passwords, roles, active state and metadata are preserved. Initial access is granted only when this run inserts `demo-granted`; a preexisting account receives no grant, and revoked grants remain revoked on single or concurrent replay. Forced password change is retained for newly seeded technicians. Injected failure before commit rolls back all seed writes. No source document is seeded.
- `/health/live` is independent liveness; `/health/ready` checks migration readiness; `/health` returns only database readiness and safe 503 on failure. `/api/v1/status` requires current unrestricted Admin identity and rechecks role after assembling its boolean-only response. No key still permits startup/admin work. Secret sentinels and driver exception text are absent from API/log output; passive GET leaves last activity unchanged and rejects exact idle cutoff. PUT is unsupported; no key editing exists.
- Vietnamese configuration uses real status calls and clears stale status on error, provides retry/loading/back navigation, and distinguishes key presence from provider connectivity. Extracted Sidebar retains current role labels, logout and existing session/activity behavior, shows configuration only for Admin and uses active-link semantics. Technician direct API requests receive 403 and direct page entry shows denial. Existing login/account/grant workflows pass after layout integration.
- `data/sample`, `data/uploads` and `storage` are preserved with empty `.gitkeep` markers; existing runtime ignores remain effective. Storage is not mounted publicly.

## Task Commits and TDD Gates

1. Task 01-04-01 RED: `75f605f` — **22 failed, 1.45s**, explicit missing snapshot/boundary assertions, no collection/syntax error.
2. Task 01-04-01 GREEN: `6d9e756` — whole-resource policy, current SQL wrapper, bounded protocols/DTOs, documentation and passing contract/ACL/full regression.
3. Task 01-04-02 RED: `e3c787f` — **10 failed, 4.38s**, missing seed behavior and health/status 404s, no collection/syntax error; browser scenario authored.
4. Task 01-04-02 GREEN: `efb3b75` — transactional seed, safe health/status, Vietnamese configuration/Sidebar and final backend/browser acceptance.
5. SUMMARY metadata: separate orchestrator commit after self-check; root also owns shared STATE/ROADMAP/REQUIREMENTS updates.

Both tasks followed RED→GREEN. Final review expanded disabled/forced-change Admin test cases without changing production policy. No refactor commit was necessary and no tracked-file deletions occurred.

## Files Created/Modified

- `backend/app/auth/policy.py`: current SQL principal seam and pure all-provenance decision.
- `backend/app/rag/{__init__,contracts}.py`, `backend/app/llm/{__init__,contracts}.py`: independent DTOs and adapter protocols.
- `backend/app/modules/{log_analysis,tickets,reports}/__init__.py`: business package boundaries only.
- `backend/tests/unit/{test_policy,test_module_boundaries}.py`: policy, current database revocation, architectural imports and DTO edges.
- `docs/{module-boundaries,security-contracts}.md`: signatures, DTO ownership and future endpoint acceptance obligations.
- `backend/scripts/seed_demo.py`, `backend/tests/integration/test_bootstrap_seed.py`: separate guarded replay-safe seed and transaction/concurrency tests.
- `backend/app/{main,api/status,api/health}.py`, `backend/tests/integration/test_startup.py`: router assembly, safe health/status and no-key/role/secret/timeout tests.
- `frontend/src/app/(workspace)/configuration/page.tsx`, `frontend/src/components/Sidebar.tsx`, `frontend/src/app/(workspace)/layout.tsx`, `frontend/tests/e2e/status.spec.ts`: real role-aware configuration and navigation.
- `data/sample/.gitkeep`, `data/uploads/.gitkeep`, `storage/.gitkeep`: empty directory preservation.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 — Required UI integration] Connect the extracted Sidebar in workspace layout**
- Task 2 listed Sidebar/configuration but the existing navigation was inline in workspace layout, omitted from its file list. A component alone would not expose Admin configuration navigation.
- Replaced inline Sidebar content through the approved ownership extension `frontend/src/app/(workspace)/layout.tsx`; preserved session resolution, expiry, activity and logout behavior.
- Commit `efb3b75`; full browser regressions pass.

**2. [Rule 1 — Test locator ambiguity] Scope configuration errors away from Next route announcements**
- First full browser run: **3 passed / 1 failed, 22.6s**. `getByRole('alert')` matched both the intended paragraph and Next.js's route announcer.
- Scoped configuration error to its named region and technician denial by error text in `frontend/tests/e2e/status.spec.ts`. Production code was unchanged.
- Commit `efb3b75`; final four browser scenarios pass.

### Execution Coordination

All staging/commits were performed centrally by the orchestrator; this executor waited for each RED/GREEN hash before continuing. No child Git escalation, cleanup, prune, installation, operational data deletion or shared planning edit was performed. Existing unrelated `.gsd/`, `docs/host-docker-storage.md` and root planning changes were preserved.

## Scope and Remaining Obligations

- SYS-04 numeric precision is a **verifier backstop**, not an arithmetic result: Phase 1 computes no report metrics or embeddings. Model/dimension/index/locator preservation is tested; numeric policy must be carried into implementing phases without inferring precision applicability from these tests.
- The descriptor-less D-10 prohibition remains a planning verification flag. This implementation exposes account/dataset/configuration capabilities only, with protocol/package contracts for later modules; the verifier must perform the designated scope review rather than automatically green the planning flag from pytest.
- Future source/retrieval/context/history/report/PDF endpoints must apply current request and final-response/file-serving policy with direct API acceptance tests. No Phase 1 test proves those absent endpoints. Already-delivered authorized responses cannot be recalled after later revocation.
- No known implementation stubs, skipped tests, unrun task checks or new unmodeled security surfaces were found. Protocol methods and empty business ownership packages are intentional phase boundaries, not deferred working features.
- Host exposure/restart/persistence and final visual usability remain Plan 05 scope. No external authentication or user setup gate was needed during this plan. The operator's separate documented bootstrap/seed commands remain intentional setup actions.

## Next Plan Readiness

Plan 05 can use current policy/contracts, separate seed command, status/health routes and configuration UI for full operational/browser acceptance. Reuse the isolated `rag_test` topology sequentially: database-reset fixtures are shared, so backend and browser suites must not run concurrently. No operational volume was removed or reseeded. Shared planning advancement belongs to the root after this SUMMARY is committed.

## Self-Check: PASSED

- All 25 realized production/test/documentation/marker files exist on disk.
- `75f605f`, `6d9e756`, `e3c787f` and `efb3b75` resolve as Git commit objects, in the required RED→GREEN order.
- Realized task diff contains no tracked-file deletions; final scoped `git diff --check` passes.
- Final task/full backend/browser/build/type/lint claims match recorded output, with no missing task verification. SUMMARY exists on disk; root-owned metadata commit follows.

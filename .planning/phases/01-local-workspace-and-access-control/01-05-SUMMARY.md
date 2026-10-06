---
phase: 01-local-workspace-and-access-control
plan: "05"
subsystem: testing
tags: [docker-compose, powershell, alembic, postgresql, pgvector, playwright, accessibility, recovery]
requires:
  - phase: 01-04
    provides: "Current authorization, provider-free status/contracts, transactional demo seed and isolated API/Web/PostgreSQL tests"
provides:
  - "Disposable operational acceptance with real empty/replayed migrations, failure startup gate, process interruption/retry, restart snapshots and actual host loopback listeners"
  - "Frontend publishing bridge correction while API/database/test networks remain private"
  - "Accessible account/grant panel focus wrapping and restoration, narrow table containment and seven real browser workflows"
  - "Bounded isolated test clock proving passive polling and exact idle/absolute browser expiry without changing host time"
affects: [local-operations, ingestion, retrieval, ticket-analysis, reporting, verification]
tech-stack:
  added: []
  patterns: [unused disposable project ownership guard, sanitized temporary Compose configuration, exact private restart snapshot, frontend dual networks, native modal with explicit keyboard wrap, isolated fixture clock]
key-files:
  created: [tools/verify-local.ps1]
  modified: [docker-compose.yml, docs/local-development.md, backend/tests/integration/test_migrations.py, backend/tests/integration/test_bootstrap_seed.py, backend/tests/support.py, frontend/tests/e2e/phase1.spec.ts, frontend/tests/e2e/accounts.spec.ts, frontend/tests/e2e/datasets.spec.ts, frontend/tests/e2e/status.spec.ts, frontend/src/app/globals.css, frontend/src/components/AccountPanel.tsx, frontend/src/components/DatasetGrantPanel.tsx]
key-decisions:
  - "Only frontend joins the publishing web bridge and internal local network; backend/database and all test services retain their private networks. Effective mapping and host listeners are checked separately from Compose/HostConfig."
  - "Acceptance refuses an existing project and replaces operational credentials/bind mounts with a temporary configuration and owned disposable volumes; it never reads operator .env or deletes operator volumes."
  - "Browser expiry clock/session introspection lives only in the already-isolated TEST_MODE fixture module, resets each scenario, and does not modify production clock code or host time."
requirements-completed: [AUTH-01, AUTH-02, AUTH-03, AUTH-04, AUTH-05, SYS-01, SYS-04]
coverage:
  - id: D1
    description: "Real Alembic empty/head/vector/constraints/replay, failed migration startup gate, bootstrap/seed process interruption/retry and exact restart persistence"
    requirement: SYS-01
    verification:
      - {kind: integration, ref: "backend/tests/integration/test_migrations.py", status: pass}
      - {kind: integration, ref: "backend/tests/integration/test_bootstrap_seed.py", status: pass}
      - {kind: other, ref: "powershell -NoProfile -File tools/verify-local.ps1 -TestProject rag-phase1-acceptance", status: pass}
    human_judgment: false
  - id: D2
    description: "Only frontend effectively publishes IPv4 loopback; actual host IPv4/IPv6 listeners, private API/database mounts and no-key startup are checked"
    requirement: SYS-01
    verification:
      - {kind: other, ref: "tools/verify-local.ps1", status: pass}
      - {kind: integration, ref: "backend/tests/integration/test_startup.py", status: pass}
    human_judgment: false
  - id: D3
    description: "Real login/role landing/logout, cookie/CSRF replay, forced change/reset/disable, empty/granted/revoked scope and permission-rejection cache clearing"
    requirement: AUTH-01
    verification:
      - {kind: e2e, ref: "frontend/tests/e2e/phase1.spec.ts", status: pass}
      - {kind: e2e, ref: "frontend/tests/e2e/accounts.spec.ts", status: pass}
      - {kind: e2e, ref: "frontend/tests/e2e/datasets.spec.ts", status: pass}
      - {kind: e2e, ref: "frontend/tests/e2e/status.spec.ts", status: pass}
    human_judgment: false
  - id: D4
    description: "Labelled modal controls, keyboard wrapping/Escape/opener focus, contained 390px table and warm ui-smoke below 30 seconds"
    requirement: AUTH-02
    verification:
      - {kind: automated_ui, ref: "frontend/tests/e2e/phase1.spec.ts#ui-smoke", status: pass}
      - {kind: automated_ui, ref: "frontend/tests/e2e/accounts.spec.ts#narrow viewport", status: pass}
    human_judgment: false
actuals:
  tokens: 13405
  tasks: 2
  commits: 5
duration: 49min
completed: 2026-10-06
status: complete
---

# Phase 1 Plan 05: Local acceptance and recovery Summary

**Disposable real migration/recovery and loopback acceptance, corrected frontend publishing, accessible Vietnamese account/grant panels and seven browser workflows with exact session cutoff proof.**

## Performance and Verification

- Execution began approximately 2026-10-06 01:27 UTC, after preceding metadata commit `2bc660b`; Task 1 RED was committed at 01:28:35 UTC. Completion approximately 02:16 UTC: 49 minutes wall time, approximately 38 minutes of active implementation/build/verification and 11 minutes of final central Git approval/coordination waiting. Docker layer/export work is included in active time; it is not ui-smoke latency.
- Two tasks and 13 realized source/test/documentation files. Actual tokens are `ceil(53619 / 4) = 13405`, measured over the UTF-8-decoded realized Git diff `2bc660b..d5b5148` restricted to those files. Planning metadata and harness tokens are excluded; five commits include four task gates and the separate root-owned SUMMARY metadata commit.
- Final exact operational command `powershell -NoProfile -File tools/verify-local.ps1 -TestProject rag-phase1-acceptance`: **exit 0; all PASS checks; 397.92s**, including image/container startup and cleanup. Selected migration/bootstrap/seed/startup pytest inside that disposable project: **21 passed, one existing warning, 21.66s**.
- Final full backend command `docker compose run --rm backend-test python -m pytest -q`: **exit 0; 76 passed, one existing warning, 44.85s**, on migrated isolated `postgres-test/rag_test`. Browser suites followed sequentially on the main test topology.
- Final focused command `docker compose run --rm frontend-test npm run test:e2e -- phase1.spec.ts --grep ui-smoke`: **exit 0; one passed; 2.6s Playwright runner**, after `docker compose up -d --wait next-test`. Measured warm scenario **1213ms** (test 1.3s), including fixture/login/labelled controls/role landing/keyboard/logout and excluding container/image startup. Full-suite smoke subsequently measured **824ms** (test 882ms). Both satisfy the 30-second contract.
- Final full browser command `docker compose run --rm --volume D:/KhacNghia/RAG/frontend/test-results:/app/frontend/test-results frontend-test npm run test:e2e`: **exit 0; seven passed, 30.6s**, one worker, no fixed sleeps. The only additional option retains ignored screenshots; no application/test logic is replaced. Narrow layout 1.2s, account recovery 3.8s, dataset grant/revocation 12.8s, clock expiry 1.8s, tracer 910ms and safe status 2.3s.
- Separate final `docker compose run --rm --no-deps frontend-test npm run typecheck` and `npm run lint`: **both exit 0** after the focus fix. Separate `docker compose run --rm --no-deps next-test npm run build`: **exit 0**, cached compile 434ms, TypeScript 1724ms, static pages 577ms. The preceding rebuilt web image also passed compile 3.6s/TypeScript 2.7s; no pins/lockfiles were changed. Runner `python -m pip check` passed.
- Read-only cleanup proof found no containers or volumes with `com.docker.compose.project=rag-phase1-acceptance`. Existing unrelated `.gsd/`, host-storage documentation and root-owned planning edits were preserved. No operational data reset, volume deletion, Docker storage mutation, prune, dependency installation or AI provider call occurred.

## Accomplishments

- The PowerShell runner requires Linux containers and Docker Engine >=28, validates resolved config without printing it, and refuses any preexisting labelled project/volume. It uses an empty temporary env file, ephemeral credentials, private test topology and owned named upload/storage volumes in place of operator bind mounts. Only the disposable frontend publishes `127.0.0.1:33071`; the original configuration is checked for frontend-only `127.0.0.1:3000` publishing. Ordinary failure exits nonzero; native Docker stderr progress is handled correctly on Windows PowerShell 5.
- Fresh PostgreSQL was verified to have no application tables before real Alembic execution. A deliberate migration exit 41 made Compose startup fail and left backend/frontend stopped. The same retained empty database then reached real `0001_access_control` head and pgvector `0.8.7`; upgrade replay twice preserved state. Integration tests exercise actual Alembic, schema constraints/immutable usernames and 503 readiness before head, never ORM `create_all`.
- Independent bootstrap processes serialize to exactly one Admin. Real seed CLI replay preserves full snapshots. New recovery tests pause a child after actual flushed account/grant writes, SIGKILL it, confirm complete rollback and retry successfully. Existing service concurrency, revoked-grant replay and injected transaction rollback tests remain in the selected and full suites.
- A disposable Admin, two technicians, dataset metadata and grant were created without AI configuration. A private digest compares all row values, including IDs, password hashes, roles, flags, metadata, grants and timestamps across PostgreSQL/backend/frontend restart; no row/hash values are printed. Exact persistence passed. Actual Docker NetworkSettings mapping and host listener inspection proved IPv4 loopback publication, with no IPv6/wildcard/LAN listener at the test port. API/PostgreSQL/test database have no host bindings; host login returned 200.
- Local operation docs now provide exact PowerShell copy/edit/setup, readiness/Alembic, interactive bootstrap `exec -it`, separate seed, logout/reset/forced-change, safe retry and binary backup instructions. They explain optional server-side keys, ignored real env files, internal networks and why effective listener checks are necessary. The root corrected the frontend topology to join private `local` plus publishing `web`; only frontend joins `web`.
- Account and grant dialogs expose `aria-busy`, native modal isolation, explicit Tab/Shift+Tab wrapping, Escape handling and opener restoration. Account Escape is blocked during an in-flight save. Shared CSS retains the desktop sidebar/table/right-panel arrangement, contains wide tables within their card at 390px, preserves mobile navigation and makes select/focus/backdrop states consistent. Mutation success remains tied to committed requests; existing partial grant failure reconciliation remains tested.
- Browser acceptance covers Admin/technician landing, no-grant guidance, forced password change/cookie rotation, reset/disable second-context revocation, grant/revoke while the technician page remains open, direct unauthorized API requests, cookie flags/CSRF replay and generic safe configuration errors. A 403 status rejection explicitly clears cached provider/database status. The test-only clock proves at least three real passive dataset GET polls, zero activity heartbeats and unchanged SQL activity timestamp; exact idle and absolute cutoffs redirect to login and clear dataset content. Absolute cutoff keeps idle valid to isolate the rule. Clock resets each scenario, is bounded/validated and exists only in the already-isolated TEST_MODE fixture module.

## Visual and Environment Evidence

The executor inspected actual screenshots in ignored `frontend/test-results/`: `phase1-desktop.png` (1280px left sidebar/table), `phase1-narrow.png` (390px account panel with visible labels/buttons and amber focus), and `phase1-narrow-workspace.png` (390px navigation, contained scrolling table and visible create/logout controls). The last screenshot was a separate browser capture with no source changes or full-suite rerun. Keyboard Tab/Escape/restore and document/panel bounds were verified by browser automation; no human keyboard or subjective usability approval is claimed.

Host read-only Windows Firewall inspection showed Domain, Private and Public profiles enabled, with default inbound action reported as `NotConfigured`. No firewall rule was changed. A probe from a separate LAN machine was not available; the docs retain that operator/environment check. The PASS evidence establishes actual local mapping/listeners on Docker **29.8.1**, not every possible external routing/VPN/firewall configuration. Docker documents pre-28 localhost/L2 limits and direct routing in [port publishing](https://docs.docker.com/engine/network/port-publishing/), and frontend/public plus backend/private attachment in [multiple networks](https://docs.docker.com/engine/network/#connecting-to-multiple-networks).

## Task Commits and TDD Gates

1. Task 01-05-01 RED: `5dd674d` — valid runnable acceptance entrypoint explicitly exited 1 because migration/recovery/listener proof was absent. Existing Alembic behavior was already implemented; the missing operational acceptance gate was the new feature.
2. Task 01-05-02 RED: `8f92d26` — **three expected assertion failures** on real UI/API: 390px document overflow (1.0s), missing account dialog `aria-busy` (6.1s), absent fixture clock route (682ms). No syntax/collection failure.
3. Task 01-05-01 GREEN: `cd6db37` — disposable runner/recovery tests/docs and root-owned frontend publishing correction; final operational acceptance passed.
4. Task 01-05-02 GREEN: `d5b5148` — accessible responsive panels, isolated clock and completed browser acceptance.
5. SUMMARY metadata: separate orchestrator commit after self-check; shared STATE/ROADMAP/REQUIREMENTS updates belong to the root.

Both tasks have RED before their respective GREEN. Task 2 test authoring was independent while the operational acceptance ran; backend/browser suites sharing one database were sequential. No refactor commit or tracked-file deletion was needed.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 — Product network bug] Frontend-only internal bridge did not effectively publish the configured port**
- Found during Task 1 after empty/replay/failure/restart checks passed: the effective mapping assertion failed although HostConfig declared loopback.
- At the executor's three-fix limit, the root independently diagnosed `NetworkSettings.Ports[3000]` as empty. A disposable dual-network probe produced a real loopback mapping, listener and HTTP 200.
- Root-owned `docker-compose.yml` adds frontend-only `web`; API/database and test networks remain internal. Approved runner/docs updates check and explain the topology.
- Final operational command passed all actual listener checks; commit `cd6db37`.

**2. [Rule 2 — Required verification seam] Extend isolated fixture support for browser exact-cutoff checks**
- Task 2 requires a controlled backend clock but only reset/proof routes existed. Root approved ownership extension of `backend/tests/support.py`.
- Added validated clock and session timestamp fixture routes, reset each scenario, without changing production auth code or host time. The production API never registers the fixture router.
- Final exact cutoff/passive browser scenario passed (1.8s), full backend 76 passed; commit `d5b5148`.

**3. [Rule 1 — Keyboard focus] Explicitly wrap focus at dialog boundaries**
- Initial GREEN ui-smoke failed after 6.3s: native modal Tab from the final button did not focus the first field, although open focus and busy semantics passed.
- Added first/last Tab and Shift+Tab wrapping in both panel components; retained native modal/Escape behavior and explicit opener restoration.
- Focused smoke and full browser suite passed on rebuilt images; commit `d5b5148`.

### Execution Issues and Coordination

- Early runner attempts exposed PowerShell function/executable name recursion, StrictMode scalar `.Count`, and native stderr progress treated as an error under `Stop`. The runner now calls `docker.exe`, wraps scalar-prone selections in arrays and checks native exit codes. All were confined to the newly introduced acceptance runner. Root handled the subsequently discovered product network bug independently after the executor's fix limit.
- Sandbox access to Docker configuration required approved tool escalation; this was filesystem execution approval, not an application/provider authentication gate. No operator secret was requested or emitted.
- All Git staging/commits were central. Final Git approval/coordination waiting is reported separately from active work and warm latency; no duplicate Git request, child Git escalation or cleanup of shared work was performed.

## Scope and Remaining Obligations

- Phase 1 behavior is verified through UI/API/SQL/real Compose execution. Existing pure composite authorization and replaceable module/provider contracts remain the foundation for later phases; these tests do not prove absent retrieval/source/history/report/PDF endpoints, ingestion, generation or numeric report precision.
- Previous planning assumption/classification flags and numeric-precision verifier backstops remain for the phase verifier; passing pytest or screenshots does not silently resolve those flags or constitute human UAT approval.
- No known implementation stubs, skipped tests, zero-test gates or unrun automated task verification remain. The external LAN-machine check is a documented environment limitation, not a claimed completed manual check. The unchanged Starlette/httpx TestClient deprecation warning is outside this task's scope.
- No external service setup or authentication gate was needed. Operator first-Admin/bootstrap/optional seed and secret configuration remain intentional documented local setup actions.

## Next Phase Readiness

Local operations, auth/accounts/dataset metadata/grants, safe configuration, module contracts and final acceptance are ready for root code review and phase verification. Docker publishing now works on actual loopback; restart and retry behavior has real database/process evidence. Future modules must apply current ACL at request and final response/file boundaries and keep deterministic database metrics separate from retrieved context. Shared planning advancement is owned by the orchestrator after this SUMMARY is committed.

## Self-Check: PASSED

- All 13 realized source/test/documentation files and this SUMMARY exist on disk.
- `5dd674d`, `8f92d26`, `cd6db37` and `d5b5148` resolve as Git commit objects; each task has RED before GREEN.
- The committed realized diff has no tracked-file deletions; scoped diff whitespace checks pass.
- Actuals recomputed from `2bc660b..d5b5148` match 53619 characters / 13405 tokens. All final automated task/full regression claims match recorded output; screenshot inspection and unrun external LAN/human approval are distinguished.
- Shared STATE, ROADMAP, REQUIREMENTS, configuration, handoff and VALIDATION files were not edited by this executor. SUMMARY metadata commit and state advancement belong to the root.

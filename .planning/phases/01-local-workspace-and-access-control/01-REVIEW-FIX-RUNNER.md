---
phase: 01-local-workspace-and-access-control
scope: runner-review-fixes
status: complete
findings: [CR-01, WR-01]
commits: [2a6bfb9, 9e74078, 17b2c87]
---

# Phase 1 runner review fixes

CR-01 and WR-01 are implemented and verified. The acceptance runner creates a unique actual Compose project per invocation, verifies ownership before using Docker resources, removes only owned resources, and restores environment/temporary files even when teardown fails.

## Changes

- **CR-01:** Check every generated volume/network name and legacy predictable name regardless of labels before provisioning. Pre-create unique external resources and inspect the run-specific/project labels before any mounting. A create-time volume reuse race with mismatched ownership is rejected. Cleanup verifies container labels, removes networks by their recorded IDs, and verifies volume labels plus creation timestamp before removal. The runner does not use `down --volumes` or orphan removal. Concurrent invocations have distinct actual projects/resources; using the same host port can still cause one invocation to fail safely.
- **WR-01:** Capture the acceptance error and teardown errors separately. Docker cleanup has an independent catch and nested finally; restoration of POSTGRES_PASSWORD/OPENAI_API_KEY/APP_ORIGIN and each temporary-file removal are always attempted. Either failure produces a nonzero result, and the final success message is emitted only after cleanup succeeds.
- **Readiness deviation, approved by orchestrator:** The first revised acceptance run failed at the empty-database query because `rag` did not yet exist, while PostgreSQL was already marked healthy. Both operational and isolated-test Compose healthchecks now use `pg_isready -h 127.0.0.1`. A deterministic initialization-hook barrier on the pinned image proved that its temporary server accepts Unix socket connections and rejects TCP; the final server accepts TCP after initialization. This addresses startup readiness directly rather than masking it with sleeps/retries in acceptance.

Changed source/test/docs: `tools/verify-local.ps1`, `tools/tests/verify-local.Tests.ps1`, `tools/tests/verify-local-sentinel.Tests.ps1`, `tools/tests/postgres-readiness.Tests.ps1`, `docker-compose.yml`, `docs/local-development.md`.

## TDD and commits

| Gate | Commit | Evidence |
| --- | --- | --- |
| Runner RED | `2a6bfb9` | Five mocked safety assertions failed against the original runner: unlabelled collision reached build/cleanup; teardown failure skipped environment/temp restoration and masked the acceptance error. No real Docker deletion was performed by the mocks. |
| Readiness RED | `9e74078` | Actual pinned-image temporary/final server distinction passed, then the assertion requiring both Compose TCP healthchecks failed. |
| GREEN | `17b2c87` | Ownership-safe provisioning/cleanup, guaranteed local restoration, TCP healthchecks, focused tests and updated operator documentation. |

Git staging/commits were performed centrally by the orchestrator. No child Git mutation was used.

## Verification

| Command | Actual result |
| --- | --- |
| `powershell -NoProfile -File tools/tests/verify-local.Tests.ps1` | Exit 0; 9 safety assertions passed. Covers unlabelled exact volume/network collisions, create-time ownership mismatch, environment restoration, temporary credential directory removal, and preservation of both acceptance and teardown errors. Docker is mocked, so cleanup failures are non-destructive. |
| `powershell -NoProfile -File tools/tests/verify-local-sentinel.Tests.ps1` | Exit 0; a random, disposable, unlabelled exact-name volume was rejected before build/start. Sentinel bytes and the volume creation timestamp remained unchanged. Only the volume created by this test was removed afterward. This test was run only after the protective implementation existed. |
| `powershell -NoProfile -File tools/tests/postgres-readiness.Tests.ps1` | GREEN exit 0 in 5.61 seconds; 3 PASS checks. Temporary server Unix socket ready/TCP unavailable, final TCP ready, both Compose healthchecks probe TCP. Uses one unique no-network container with tmpfs PostgreSQL storage and a temporary initialization barrier; container and hook were cleaned. |
| `powershell -NoProfile -File tools/verify-local.ps1` | Final coordinated run exit 0 in **160.97 seconds**, including successful ownership-verified cleanup. Required migration/bootstrap/seed/startup subset: **21 passed, 1 warning in 18.28 seconds**. No separate broad backend/frontend suites were rerun for this fix. |

Final acceptance PASS evidence: Docker 29.8.1/Linux; configured frontend-only loopback binding; internal local/test networks; frontend-only web bridge; private mounts; exact names unused regardless of labels; fresh PostgreSQL has no application tables; failing migration rejects startup and leaves backend/frontend stopped; real Alembic head `0001_access_control` and pgvector `0.8.7`; Alembic replay twice; required tests execute; exact account/password/role/dataset/grant snapshot survives restart; postgres/backend/postgres-test have no host bindings; actual Docker mapping is IPv4 loopback only; actual IPv4/IPv6 host listener inspection found only `127.0.0.1`; host login responds without an AI key; locked backend packages compatible; all acceptance checks and owned cleanup succeeded.

The first revised acceptance run exited 1 at the fresh PostgreSQL query (`database "rag" does not exist`). Its teardown completed without a teardown error. The pinned-image readiness proof justified the two-line Compose correction before the successful final run. An initial sentinel-test null-label assertion was corrected in the harness; the sentinel test's own volume was cleaned. An approval-delayed readiness call was interrupted before a returned session; reconciliation found no pending proof container. The orchestrator and child subsequently completed separate uniquely named proof runs with the same RED result; no proof run remains active.

## Limits and preserved scope

No operator volumes, operator `.env`, Docker storage, host clock, firewall or LAN configuration were changed. No OpenAI API calls were required. Test data remained in disposable owned storage and isolated `postgres-test/rag_test`. These checks do not claim human visual approval or a remote-machine LAN probe. The reported pytest subset had one warning; its detailed warning text was not retained by the runner's summary-only output. UI fixes and broad suite results belong to the separate UI executor's evidence. Independent re-review and phase verification remain orchestrator work.

Primary references: [Docker volume create reuse semantics](https://docs.docker.com/reference/cli/docker/volume/create/), [Docker network create and labels](https://docs.docker.com/reference/cli/docker/network/create/), [official PostgreSQL entrypoint temporary-server sequence](https://github.com/docker-library/postgres/blob/master/docker-entrypoint.sh). The readiness conclusion is also backed by the actual pinned-image barrier test rather than relying solely on upstream source.

## Self-check: PASSED

All six changed source/test/documentation files exist. RED commits `2a6bfb9` and `9e74078` and GREEN commit `17b2c87` were confirmed by the orchestrator's central commit results. The final acceptance result includes teardown success; no additional test or cleanup remains pending in this executor.

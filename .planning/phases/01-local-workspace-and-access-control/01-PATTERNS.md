# Phase 1: Local Workspace and Access Control - Pattern Map

**Mapped:** 2026-10-03
**Files analyzed:** 41 proposed file assignments (some rows group companion scaffolding files)
**Analogs found:** 0 / 41

## Evidence and Naming Status

This is a greenfield repository. `git ls-files` lists 13 tracked files: AGENTS.md and planning artifacts only. Root discovery finds `.git`, `.planning`, and `AGENTS.md`; neither `.codex/skills` nor `.agents/skills` exists. There is no tracked application source, component, authentication helper, migration, Compose configuration, or test to copy. No install/runtime mirror is used as an analog. Research and context are design inputs, not code analogs.

Context locks parent directories and behaviors, not every leaf filename. The leaf names below are **proposed planning assignments**, inferred from CONTEXT and RESEARCH; the planner may consolidate or rename them while preserving responsibility boundaries. Explicit research test paths and configuration paths are retained. Package versions in RESEARCH are candidates with unresolved execution gates, not proven repository conventions.

## File Classification

All entries are new; closest analog and match quality are `none` for every row.

| New File / Assignment | Role | Data Flow | Closest Analog | Match Quality |
|---|---|---|---|---|
| `docker-compose.yml` | config | event-driven, file-I/O | none | none |
| `.env.example`, `.gitignore` | config | file-I/O | none | none |
| `backend/Dockerfile`, `backend/.dockerignore` | config | batch | none | none |
| `backend/pyproject.toml`, `backend/requirements.lock` | config | batch | none | none |
| `backend/app/main.py` | controller | request-response | none | none |
| `backend/app/config.py` | config | file-I/O | none | none |
| `backend/app/database/session.py` | provider | request-response | none | none |
| `backend/app/database/models.py` | model | CRUD | none | none |
| `backend/alembic.ini`, `backend/alembic/env.py` | config | batch | none | none |
| `backend/alembic/versions/0001_access_control.py` | migration | batch | none | none |
| `backend/app/auth/passwords.py` | utility | transform | none | none |
| `backend/app/auth/sessions.py` | service | CRUD | none | none |
| `backend/app/auth/policy.py` | utility | request-response | none | none |
| `backend/app/auth/csrf.py` | middleware | request-response | none | none |
| `backend/app/auth/rate_limit.py` | service | CRUD | none | none |
| `backend/app/api/dependencies.py` | middleware | request-response | none | none |
| `backend/app/api/schemas.py` | model | transform | none | none |
| `backend/app/api/errors.py` | utility | request-response | none | none |
| `backend/app/api/{auth,users,datasets,status,health}.py` | route | request-response | none | none |
| `backend/app/auth/accounts.py` | service | CRUD | none | none |
| `backend/app/database/datasets.py` | service | CRUD | none | none |
| `backend/scripts/bootstrap_admin.py` | utility | batch | none | none |
| `backend/scripts/seed_demo.py` | utility | batch | none | none |
| `backend/app/{rag,llm}/__init__.py`, `backend/app/modules/{log_analysis,tickets,reports}/__init__.py` | config | transform | none | none |
| `frontend/Dockerfile`, `frontend/.dockerignore` | config | batch | none | none |
| `frontend/package.json`, `frontend/package-lock.json`, `frontend/tsconfig.json` | config | batch | none | none |
| `frontend/next.config.ts` | config | request-response | none | none |
| `frontend/src/app/layout.tsx`, `frontend/src/app/globals.css` | component | request-response | none | none |
| `frontend/src/app/login/page.tsx` | component | request-response | none | none |
| `frontend/src/app/change-password/page.tsx` | component | request-response | none | none |
| `frontend/src/app/(workspace)/layout.tsx` | component | request-response | none | none |
| `frontend/src/app/(workspace)/{accounts,datasets,configuration}/page.tsx` | component | CRUD | none | none |
| `frontend/src/components/{Sidebar,AccountPanel,DatasetGrantPanel}.tsx` | component | event-driven | none | none |
| `frontend/src/lib/api.ts`, `frontend/src/lib/contracts.ts` | utility | request-response, transform | none | none |
| `frontend/src/hooks/use-session.ts` | hook | event-driven | none | none |
| `frontend/playwright.config.ts`, `frontend/tests/e2e/phase1.spec.ts` | test | request-response | none | none |
| `backend/tests/conftest.py` | test | batch | none | none |
| `backend/tests/unit/{test_policy,test_session_clock}.py` | test | transform | none | none |
| `backend/tests/integration/{test_auth,test_admin_users,test_acl}.py` | test | CRUD, request-response | none | none |
| `backend/tests/integration/{test_bootstrap_seed,test_startup}.py` | test | batch, file-I/O | none | none |
| `docs/{local-development,security-contracts,module-boundaries}.md` | config (documentation) | transform | none | none |

`data/sample`, `data/uploads`, and `storage` are directory/volume boundaries, not implemented ingestion artifacts. Add only placeholders if needed to preserve empty directories. Package `__init__.py` scaffolding elsewhere is mechanical and follows the owning module assignment.

## Pattern Assignments

### Deployment and dependency files (rows 1–4, 25–27)

**Analog:** None. Use RESEARCH → Standard Stack / Installation and version validation gate / Bootstrap, seed and Compose patterns.

Compose dependency order: PostgreSQL health → successful one-shot Alembic migration → API readiness → frontend. Publish only frontend on loopback; API/database stay internal. Persist PostgreSQL with a named volume and uploads/storage locally; never expose storage as a public static directory. Test profiles use isolated databases and matching browser runner images. Pin/lock dependencies after the execution compatibility gate; no `latest` images. `.env.example` contains placeholders; ignore real env files, runtime storage and generated artifacts. OpenAI key is optional and server-side. Docker readiness remains an execution prerequisite; this artifact claims no successful runtime checks.

### Backend assembly, settings and database (rows 5–10)

**Analog:** None. Use RESEARCH → Responsibility Map / Patterns 1 and 4.

`main.py` assembles routes, error handling and lifecycle without creating provider clients. Typed settings own database/secrets/origin configuration. One synchronous SQLAlchemy Session per request; synchronous handlers for synchronous DB work. Models own account, opaque-session digest, dataset, grant, administration guard and bounded login-rate-limit persistence. UUID keys, unique normalized usernames/session digests/grant pairs and UTC timestamps belong in the initial migration. Alembic owns upgrades; no startup `create_all`. The guard row exists before concurrent bootstrap/role/active mutations use it.

### Authentication and request guards (rows 11–19)

**Analog:** None. Use RESEARCH → Patterns 1–3 / Endpoint contracts.

Separate hash/verify, session lifecycle, capability/dataset policy, CSRF, throttling and request dependency wiring. Route handlers validate DTOs and call services. Session resolver reads current account/session, rejects revocation and expiry before activity updates, then enforces forced-password state. Unsafe requests require exact Origin, JSON/custom header and session-bound CSRF where authenticated. DTOs never return password hashes, temporary passwords or session digests. Error wrappers give consistent machine code/Vietnamese text without hidden dataset metadata; protected responses are `no-store`.

### Account and dataset mutations (rows 20–21)

**Analog:** None. Use RESEARCH → Pattern 4 / Endpoint contracts.

Services own transaction boundaries, rollback and invariants. All last-active-Admin-changing operations and bootstrap lock the same guard row, then check counts within that transaction. No account hard delete or dataset delete. Reset/disable/role changes revoke relevant sessions atomically. Dataset list/count queries filter current grants before pagination. Per-item PUT/DELETE grants are idempotent and only target technicians; metadata mutation is Admin-only. Keep this database-backed dataset service free of parser/RAG/provider imports.

### CLI and future module boundaries (rows 22–24)

**Analog:** None. Use CONTEXT D-02/D-15 and RESEARCH → Bootstrap / seed patterns.

Bootstrap and seed are separate interactive commands with `getpass`; reuse database/service contracts. Bootstrap creates at most one first Admin and never overwrites an account. Seed inserts metadata plus granted/ungranted technicians; add initial grants only for a technician newly inserted by that run. Replay never restores revoked grants or changes existing passwords/roles/metadata. Keep rag/llm/modules as explicit boundary scaffolding and documentation only; no fake endpoints, provider calls, LangChain pipeline, report UI or source processing in Phase 1.

### Frontend pages, components and API transport (rows 28–35)

**Analog:** None. Use CONTEXT D-10–13/D-16–17 and RESEARCH → CSRF transport / Endpoint contracts / UI paragraph.

Use App Router with relative `/api/v1` requests forwarded to FastAPI through the same-origin Next configuration. Validate actual proxy Set-Cookie/Origin behavior before expanding features. Shared API client carries CSRF, interprets machine errors and clears stale protected state on 401/403. Session hook handles real interaction activity separately from passive polling; no localStorage auth token. Forced-change page precedes the workspace shell. Admin lands on accounts; technician on datasets. Sidebar, tables and right panels are real backend flows; save awaits committed success then refreshes authoritative data. Vietnamese empty/error/loading labels and accessible focus apply across pages. Configuration displays safe status and “Chưa cấu hình AI”, with no API-key textbox. UI guards complement backend enforcement.

### Tests and operational documentation (rows 36–41)

**Analog:** None. Use RESEARCH → Validation Architecture / Fixtures and assertions.

Fixtures migrate an isolated PostgreSQL database, inject a UTC clock and provide independent connections for concurrency checks. Unit tests cover role capabilities, default deny, composite provenance and expiry boundaries; integration tests cover actual session/revocation/forced-change/ACL/admin transactions and seed replay. Browser tests verify cookies/CSRF/proxy, two-client revocation, routing and Vietnamese states. Outbound transport must fail on any AI request. Never use SQLite to establish PostgreSQL locking correctness or clean production/demo data as test setup. Operational docs distinguish bootstrap from seed, explain local binding/env/no-key startup, and list carry-forward source/history/PDF ACL obligations without claiming those endpoints exist.

## Shared Patterns

These are required new contracts derived from upstream decisions, **not extracted existing patterns**. No authentic code excerpt or source line range exists to reproduce.

| Concern | Proposed owner | Apply to | Required contract |
|---|---|---|---|
| Authentication lifecycle | `backend/app/auth/sessions.py` | all protected routes | current account/session; idle 30 minutes, absolute 8 hours; passive polling does not renew |
| Authorization | `backend/app/auth/policy.py` | metadata now; later sources/history/reports/PDF | deny unknown roles; current grants; whole-resource all-dataset policy; deny missing technician provenance |
| Forced password change | `backend/app/api/dependencies.py` | all business/admin routes | restricted account reaches only auth helpers, password change and logout |
| Transactions | `backend/app/database/session.py` + services | all mutations/CLI | request-scoped Session; explicit transaction; guard lock before last-admin count; rollback on failure |
| Errors and DTO validation | `backend/app/api/{errors,schemas}.py` | every API handler | 401/403/404/409/422/429 contracts; safe generic missing dataset; write-only secret inputs |
| Secret-safe configuration/audit | settings and mutation services | API, CLI, docs, status | no raw passwords/tokens/keys/DSNs in logs or DTOs; safe audit actor/action/object identifiers |
| Same-origin transport | `frontend/next.config.ts`, `frontend/src/lib/api.ts` | all browser API operations | cookie/CSRF/Origin preserved; no shared caching or localStorage token |
| Future modularity | boundary docs and policy | future modules/providers | backend owns identity/policy; RAG consumes authorized scope; provider types separate; no initialization now |

## No Analog Found

Every file assignment in File Classification has no codebase analog because tracked source is absent. Planner should cite the exact CONTEXT decision and RESEARCH section given in Pattern Assignments, and define each new contract explicitly. Do not substitute examples from plugin installations or mark new scaffolding as existing reusable code.

## Dependency Order for Planning

1. Resolve execution prerequisites and establish deployment/package/config scaffolding.
2. Establish schema, migrations, settings and database lifecycle.
3. Build a walking skeleton: bootstrap Admin → same-origin Web login → authenticated filtered dataset read → logout/replay rejection.
4. Extend session guards, account mutations, forced change and dataset grants with concurrency/revocation tests.
5. Finish shared UI flows, replay-safe seed, safe status, policy/module docs and full browser/startup/persistence validation.

Schema and API DTO contracts must stabilize before independent UI/API tasks expand. Shared transaction/policy/session modules require clear ownership across plans. Bootstrap and administrative mutations share the same last-admin lock contract. Future AUTH-04/05 endpoints remain carry-forward obligations, not Phase 1 completion evidence.

## Metadata

**Analog search scope:** full tracked repository inventory and root/application/skill directory discovery.
**Tracked files scanned:** 13 paths; 0 implementation candidates.
**Inputs read:** AGENTS.md, 01-CONTEXT.md, 01-RESEARCH.md.
**Pattern extraction date:** 2026-10-03.
**Coverage:** 0 exact, 0 role-match, 41 no-analog assignments.
**Tool availability:** dedicated Read/Write tools are unavailable; read-only PowerShell discovery/reads and apply_patch used solely for this artifact. No source edits, installs or commits.

# Walking Skeleton — Modular RAG cho IT & Logistics
**Phase:** 1
**Generated:** 2026-10-03
**Status:** Architectural execution contract; no application/test evidence yet.

## Capability Proven End-to-End
Planned proof: operator bootstraps Admin; real browser login through same-origin Next → FastAPI creates PostgreSQL session; user sees authorized dataset metadata and logout rejects replay.
**As a** Admin hoặc Kỹ thuật viên, **I want to** mở ứng dụng local, đăng nhập và truy cập đúng phạm vi được cấp quyền **so that** sử dụng nền tảng RAG an toàn.
The story paraphrases approved context, preserving the authoritative ROADMAP goal.

## Architectural Decisions
| Decision | Choice | Rationale |
|---|---|---|
| Web/API | Next.js App Router + TypeScript / FastAPI sync handlers | Locked user stack; Web owns presentation, backend owns policy/services |
| Data | PostgreSQL18 + pgvector; SQLAlchemy2 and Alembic | Local relational source of truth; vector extension ready, no vector retrieval in Phase1 |
| Auth | Argon2; opaque digest sessions; session-bound CSRF; username | D-01/03/04, current backend revocation, real proxy cookie proof |
| Session | 30min idle / 8h absolute; real interaction POST, polling passive | Exact D-04; rotation preserves absolute deadline |
| Authorization | auth.policy role capabilities + live dataset grants | D-05–09, whole-resource provenance contract independent of RAG |
| Deployment | Docker Compose, frontend 127.0.0.1 only, API/DB internal | D-14; durable DB volume and private local upload/storage mounts |
| Migration | One-shot Alembic upgrade head before API readiness | Actual schema proof, no ORM startup auto-creation |
| Directory | backend/app/{api,rag,llm,database,auth,modules/{log_analysis,tickets,reports}}, frontend, data, storage, docs | User-locked structure |
| Providers | Separate typed embedding and LLM contracts, no clients now | SYS-04 boundary; real provider work Phase3 |
| Versions | Official metadata/constraints → resolved exact locks and image digests during execution | Registry candidate observations do not prove compatibility |

Reversibility: unpublished local DTO/schema contracts are costly, versioned by /api/v1 and Alembic; no one-way external contract or production data exists. Locked user choices are already authorized. No fabricated decision checkpoint.

## Stack Touched in Phase 1
- [ ] Scaffold/build/lint/test runner — 01-01 (draft, execution pending).
- [ ] Real routing and interactive browser — 01-01 tracer.
- [ ] PostgreSQL read/write and Alembic applied — 01-01; restart proof 01-05.
- [ ] Full local run command — docker compose up --build -d, then docker compose exec -it backend python -m scripts.bootstrap_admin.
- [ ] Account/reset/grant/status/demo expansions — 01-02–04.

## Out of Scope
Ingestion/source lifecycle Phase2; LangChain retrieval and real provider calls Phase3; ticket analysis Phase4; reports/PDF Phase5. Policy contracts alone do not implement those endpoints. OCR/MCP/scheduler/Agent/real connectors/email recovery/language switch/LAN remain deferred.

## Dependency Graph and File Ownership
| Plan | Wave | Needs | Creates / user capability |
|---|---|---|---|
| 01-01 | 1 | Docker Linux Engine/Compose prerequisite | Scaffold, migration/schema, bootstrap, authentication, real browser DB path; session expiry/activity |
| 01-02 | 2 | 01-01 auth/models/DTO/client | Account management, reset/forced change, limiter and admin race invariant |
| 01-03 | 3 | 01-02 user routes/session/UI | Metadata/grants and live ACL across two clients |
| 01-04 | 4 | 01-03 stable policy/admin flow | Composite policy/provider/module contracts, seed/status/configuration |
| 01-05 | 5 | all workflows | Actual migration/restart/binding proof and complete user acceptance |

Each plan owns its listed files while active; later overlapping files require prior SUMMARY and preserve prior behavior. Sequential waves reflect real shared policy/DTO/client/tests, not arbitrary chaining. 2 tasks each. No same-wave overlap.
Sizing: calibration factor1, sample_count0, confidence low; raw=calibrated 48000/28000/28000/26000/26000. Explicit coherent greenfield/full-stack slice file-count exception is authorized by orchestrator; task lists never hide touched files. Context remains below 50% target. Phase boundary cannot be narrowed to satisfy filename count.

## Multi-Source Coverage Audit
| Source | ID/item | Plan | Status | Notes |
|---|---|---|---|---|
| GOAL | Local Web login/account/dataset/module foundation | 01-01–05 | COVERED | Real frontend/API/DB tracer before expansion |
| REQ | AUTH-01 | 01-01/02/05 | COVERED | Sessions/logout/disable/rotation |
| REQ | AUTH-02 | 01-02/05 | COVERED | Create/role/disable/reset/last Admin |
| REQ | AUTH-03 | 01-01/03/05 | COVERED | Current dataset metadata/grants |
| REQ | AUTH-04 | 01-03/04/05 | COVERED | Metadata now; policy plus later endpoint obligations |
| REQ | AUTH-05 | 01-03/04/05 | COVERED | Extensible role map and Admin global report contract |
| REQ | SYS-01 | 01-01/04/05 | COVERED | Compose/pgvector/private storage; providers Phase3 |
| REQ | SYS-04 | 01-01–05 | COVERED | Real Web API + typed module/provider boundaries |
| CONTEXT | D-01/D-02/D-04 | 01-01/02 | COVERED | Username, bootstrap, session |
| CONTEXT | D-03 | 01-02 | COVERED | Forced password recovery |
| CONTEXT | D-05/D-06 | 01-03 | COVERED | Dataset ACL/default zero |
| CONTEXT | D-07 | 01-04 | COVERED | A+B whole-resource denial contract |
| CONTEXT | D-08/D-09 | 01-03/04 | COVERED | Capability separation/live backend permission |
| CONTEXT | D-10/D-11/D-12/D-13 | 01-02/03/04/05 | COVERED | Role landing/sidebar/Vietnamese/right panels |
| CONTEXT | D-14 | 01-01/05 | COVERED | Actual loopback sockets |
| CONTEXT | D-15 | 01-04/05 | COVERED | Distinct replay-safe seed |
| CONTEXT | D-16/D-17 | 01-01/04/05 | COVERED | No-key startup/secret-safe env/status |
| RESEARCH | Runtime/package names, candidates, lock compatibility, Docker absent | 01-01/05 | COVERED | Execution prerequisite/check; no claim installs ran |
| RESEARCH | Opaque sessions/CSRF/origin/no-store/DTO/error contracts | 01-01/02/03 | COVERED | Tests at real proxy and API |
| RESEARCH | Normalization/password limits/dummy verify/bounded limiter | 01-01/02 | COVERED | Boundary/unknown/race cases |
| RESEARCH | Guard-row invariant and bootstrap races/transaction rollback | 01-01/02/05 | COVERED | Independent PostgreSQL connections |
| RESEARCH | Grant filter/count/idempotent per-item writes/current response checks | 01-03 | COVERED | Revoke during request included |
| RESEARCH | Whole-resource provenance/Admin/custom role/import boundaries | 01-04 | COVERED | Policy tests, future endpoint contracts |
| RESEARCH | Health/migration readiness/seed replay/private volumes/status | 01-01/04/05 | COVERED | Real empty/repeated Alembic, persistence |
| RESEARCH | Isolated migrated DB/clock/outbound deny/browser/security/host smoke | 01-01–05 | COVERED | VALIDATION mapped, no executed proof |
| RESEARCH | Architecture responsibility map | 01-01–05 | COVERED | Backend policy/service, browser UI, DB transactions; no frontend business logic |
| RESEARCH | Package human-checkpoint recommendation | 01-01 | COVERED | Superseded by explicit developer instruction: heuristic SUS is not malicious proof; official source/version/locks checked in execution |
| RESEARCH | Future OCR/RAG/Agent/scheduler/report implementation | other phases | EXCLUDED | Explicit scope boundary, contracts only |

## Spec-less Probe Audit
Input was seven exact requirement texts; engine returned8 rows (no shape override). No SPEC sections supplied.
| Requirement | Category | Lifecycle/verification | Authored destination |
|---|---|---|---|
| AUTH-01 | concurrency | resolved/explicit | 01-01 truths: revoke/activity committed race semantics; 01-02 atomic disable/reset tests |
| AUTH-02 | unclassified | unresolved/flagged | 01-02 truth; retain classification assumption, not auto-resolved |
| AUTH-03 | unclassified | unresolved/flagged | 01-03 truth |
| AUTH-04 | unclassified | unresolved/flagged | 01-03 truth |
| AUTH-05 | unclassified | unresolved/flagged | 01-03 truth |
| SYS-01 | concurrency | resolved/explicit | 01-01/05 truths, guard/migration/replay tests |
| SYS-04 | boundary | resolved/explicit | 01-04 truth/DTO locator/model/index bounds |
| SYS-04 | precision | resolved/backstop, flagged scope mismatch | 01-04 structured truth; no arithmetic invented |

No silent drops:8 surfaced =3 explicit +1 backstop +4 unresolved flags. Backstop abstains to human_needed if no explicit evidence; unclassified rows never auto-dismissed.
Prohibition recall examined all7 requirements: auth impersonation/escalation/token leakage/CSRF/injection and generic retention are canon-security breadcrumbs to $gsd-secure-phase, dropped as duplicate canon. Routine validation/race concerns go to edge/tests. Three bespoke product prohibitions retained descriptor-less in must_haves.prohibitions: localhost must not turn LAN; administration must not require paid AI or falsely portray local AI processing; deferred features must not be represented as working. Lifecycle unresolved/flagged-unverified; no invented wired-check descriptor. They are not silently greened by ordinary pytest.

## Hook Results
API scope detector ran on nonempty concatenated Phase1 ROADMAP section plus all five PLAN bodies: detected:false, signals:[], no skipped flag. Phase1 integrates no external AI API/service; Web calls local FastAPI and PostgreSQL only. No matrix/checkpoint required.
Assumption-delta detected:false supplied by orchestrator. UI gate frontend:true/hasFrontendEvidence:false/hasUiSpec:false/block:false; no UI-SPEC obligation.
Schema gate known ORM patterns do not match Alembic; mandatory real Alembic apply/test is explicitly present regardless.

## Subsequent Slice Plan
Phase2 upload and source provenance; Phase3 grounded retrieval/providers; Phase4 logistics analysis; Phase5 deterministic reports/PDF; Phase6 reliability acceptance. All use current backend policy, original source versions and independent adapters.

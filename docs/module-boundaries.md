# Module contracts

FastAPI routes own request validation and call backend services. PostgreSQL is canonical for identity, grants, structured operational records and future report metrics. Next.js is the Web layer and same-origin API transport; it does not decide business permissions.

## Authorization and ownership

`auth.policy.current_principal(db, account) -> Principal` reloads the active account and current grants with SQL. `require_all_datasets(principal, provenance_ids, capability)` is a pure whole-resource decision; `authorize_resource(db, account, provenance_ids, capability)` connects current SQL to that policy. Snapshots are internal, never browser-supplied authority. Consumers must call again just before returning content/file bytes, not reuse an earlier snapshot after long work.

RAG receives `AuthorizedScope(dataset_ids)` from its authorized caller. It never decides roles, capabilities or grants. All retrieval branches and context assembly must apply that scope and active source versions. Admin global report-read is policy-owned; a future caller resolves the available IDs for retrieval rather than sending roles into RAG. Empty technician provenance denies the entire resource. A report built from A+B is wholly denied after A revoke; a new B-only resource can pass. The error is generic `permission_changed` without withdrawn identifiers.

## Replaceable adapters

| Boundary | Signature | Responsibility |
|---|---|---|
| Parser | `parse(content: bytes, locator: SourceLocator, dataset_id: UUID) -> tuple[EvidenceChunk, ...]` | Format adapter preserves source/version and locations; future service owns file limits/lifecycle |
| Chunker | `chunk(evidence: EvidenceChunk) -> tuple[EvidenceChunk, ...]` | Preserve provenance through splitting |
| EmbeddingProvider | `index: EmbeddingIndex`; `embed(texts: tuple[str,...]) -> tuple[tuple[float,...],...]` | Independently configured model, dimension, index version; future adapter validates vector shape/finite values |
| Retriever | `retrieve(request: RetrievalRequest) -> tuple[EvidenceChunk,...]` | Receives bounded query and authorized scope |
| LLMProvider | `generate(request: GenerationRequest) -> GenerationResult` | Selected evidence only, citation-bearing output; separate from embeddings |

Contracts import without API keys, environment settings, LangChain or OpenAI clients. Future LangChain/OpenAI implementations belong in adapters and must be resolved/pinned before installation. Auth/database/business modules must not directly import those implementations. The business packages are ownership boundaries only; Phase 1 offers no analysis, source, report or PDF endpoints.

## DTO bounds and contract synchronization

Pydantic owns backend validation/schema. Current API DTOs are exposed by FastAPI OpenAPI; frontend `src/lib/contracts.ts` mirrors them and must be updated with endpoint schema changes, verified against real API/browser tests. Internal RAG DTOs are not public endpoints or permission credentials. When future routes expose them, connect their request/response schemas to OpenAPI and regenerate or explicitly synchronize frontend contracts.

| Field | Inclusive bound |
|---|---|
| Source ID / index version / dataset IDs | UUID; required |
| Source version and optional page/row/event/record | 1–2147483647; integers, no bool/string coercion |
| Optional section/sheet | 1–512 characters if supplied |
| AuthorizedScope dataset count | 1–10000 |
| Model | 1–128 characters |
| Embedding dimension metadata | 1–65536 |
| Retrieval query / generation question | 1–8000 characters |
| Evidence / generated text | 1–32000 characters |
| Selected evidence / returned citations count | 1–100 |

Optional locator fields may be absent only alongside valid source ID/version. Extra DTO fields are forbidden; DTOs are immutable and UUID/model/dimension/index metadata survives JSON round-trip. These are transport/input bounds, not model selection or a promise every provider supports each dimension. Future ingestion/retrieval services must redact secrets before chunk/query embedding and generation; apply provider-specific limits and total evidence budgets before external calls.

Report totals must come from deterministic canonical database aggregation, never top-k chunks. Phase 1 performs no metrics arithmetic or embedding calculation. SYS-04 numeric precision applicability remains a verifier backstop and must be carried into phases implementing those calculations; boundary preservation tests do not prove future arithmetic precision.

Validation APIs follow the official [Pydantic fields](https://docs.pydantic.dev/latest/concepts/fields/) and [configuration](https://docs.pydantic.dev/latest/concepts/config/) documentation, verified with the locked runtime.

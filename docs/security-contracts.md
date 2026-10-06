# Current authorization and future endpoint obligations

Phase 1 enforces current SQL identity/grants for metadata and documents contracts for later endpoints. Capability mapping remains in backend auth, outside RAG. Unknown roles deny by default; an explicit new capability mapping can add a scoped role without changing RAG. Active Admin has global report-read authority. Technician ticket analysis/input is separate from repository upload/delete/reindex, which remains Admin-only.

Whole-resource policy requires nonempty complete provenance for scoped roles: A+B cannot be reduced to B after A revoke. Deny the entire response/PDF with generic `permission_changed`, expose no withdrawn identifiers and permit a newly authorized B-only resource. Current SQL snapshots must be refreshed at request authorization and before content/file response. Never accept an AuthorizedScope or Principal submitted by a browser as authoritative.

## Required acceptance checks when future endpoints are introduced

| Phase | Endpoint/service obligations | Direct API acceptance evidence required |
|---|---|---|
| 2: sources | Source read/download, upload/lifecycle/delete/reindex; active version, opaque local path, no public storage mount | Anonymous/unauthorized/revoked source requests return no content or sensitive identifiers; technician cannot manage repository; revoke between lookup and serving blocks bytes |
| 3: retrieval | Dense/text/exact branches, counts, selected context and history all scoped to current grants/active source versions; final recheck | Call every retrieval branch directly outside UI; revoked/unauthorized datasets never enter results, citations, context, history or final output; inject revocation during generation |
| 4: ticket input | Explicit ticket-input/analysis capability independent of shared repository management; analysis limited to authorized evidence | Technician can submit permitted ticket input but cannot upload/delete/reindex the repository; unauthorized evidence/context rejected |
| 5: reports | Report creation, list/detail/history/PDF and file serving use all provenance datasets at request and final response | A+B wholly denies after A revoke without partial text/PDF or withdrawn identifiers; newly scoped B passes; Admin global read passes; missing technician provenance denies; direct PDF URL cannot bypass auth |

Future tests must use current backend policy and real endpoint behavior, including pre-response races. UI hiding and Phase 1 policy tests do not satisfy these future endpoint acceptance checks. Once bytes have been legitimately delivered they cannot be recalled; subsequent reads always recheck current state.

Embedding and generation are distinct external trust boundaries. Future adapters redact secrets and enforce chunk/query/selected-evidence limits; never send unnecessary original files. Provider credentials remain server-side, cloud tracing disabled by default. Reports use deterministic database metrics plus evidence-backed narrative. No real-system actions, Agent tools, OCR or scheduler is authorized by these contracts.

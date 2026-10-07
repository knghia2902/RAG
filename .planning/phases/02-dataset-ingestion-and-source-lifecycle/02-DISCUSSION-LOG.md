# Phase 2: Dataset Ingestion and Source Lifecycle - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-10-07  
**Phase:** 2-Dataset Ingestion and Source Lifecycle  
**Areas discussed:** Batch upload and source versions; Structured source schemas and invalid rows; Ingestion progress and retry; Source preview and deletion

---

## Batch upload and source versions

| Option | Description | Selected |
|--------|-------------|----------|
| Hash-based no-op and immutable content versions | Same dataset/checksum is idempotent; changed file content creates a version; old active version remains until validation. | ✓ |
| Always create a new version | Every upload creates a new version even when bytes are unchanged. | |
| Replace the file in place | Overwrite current content without preserving immutable versions. | |

**User's choice:** `[auto]` Recommended default selected by the autonomous discuss mode; no interactive answer was requested.  
**Notes:** Per-file batch outcomes, immutable provenance, and no duplicate work make retries/reuploads reviewable while preserving the last known-good version.

---

## Structured source schemas and invalid rows

| Option | Description | Selected |
|--------|-------------|----------|
| Select a published profile; invalid required rows fail activation | Admin chooses a declared source profile; row-level errors are visible and the new version stays inactive if required data is invalid. | ✓ |
| Infer a profile and activate only valid rows | Infer business meaning and silently omit rows that fail validation. | |
| Store files as unvalidated raw text | Avoid typed validation and import files as generic text. | |

**User's choice:** `[auto]` Recommended default selected by the autonomous discuss mode; no interactive answer was requested.  
**Notes:** Explicit profiles avoid silently misreading logistics fields; a partial ready dataset could hide orders/incidents and distort future retrieval or reports.

---

## Ingestion progress and retry

| Option | Description | Selected |
|--------|-------------|----------|
| Persistent background jobs with visible states and safe retry | Status survives reload/restart; a failed source can be retried without duplicates. | ✓ |
| Synchronous upload and reupload on failure | Keep parsing in the HTTP upload request and require a fresh upload after failure. | |
| Browser-only status | Keep status only in the current browser session. | |

**User's choice:** `[auto]` Recommended default selected by the autonomous discuss mode; no interactive answer was requested.  
**Notes:** Parsing can be heavy; durable status and idempotent retries are necessary for the Phase 2 acceptance criteria. Queue/broker details remain for research/planning.

---

## Source preview and deletion

| Option | Description | Selected |
|--------|-------------|----------|
| Permission-checked parsed preview and immediate logical delete | Show an exact parsed excerpt/locator; tombstone immediately and clean storage after jobs are fenced. | ✓ |
| Public/static file links | Expose original files by URL and remove them later. | |
| Retain retrievability through cleanup | Keep deleted source content accessible while background cleanup runs. | |

**User's choice:** `[auto]` Recommended default selected by the autonomous discuss mode; no interactive answer was requested.  
**Notes:** Current dataset grants and active-version state must be checked at the backend response boundary. Local paths/public URLs are not source citations.

---

## the agent's Discretion

- Exact profile field definitions, parser/library, file/batch/resource limits, worker/broker and bounded retry/backoff details.
- UI layout, status refresh mechanism, and persistence/cleanup implementation, as long as the locked source lifecycle and access behavior remain intact.

## Deferred Ideas

None from this discussion; roadmap-deferred OCR, RAG/providers, ticket analysis, reports/PDF, MCP, Agent/tools, real-system connectors, and scheduler remain out of this phase.

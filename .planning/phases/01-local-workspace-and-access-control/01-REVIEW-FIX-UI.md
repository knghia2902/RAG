---
phase: 01-local-workspace-and-access-control
review: 01-REVIEW.md
findings: [CR-02, CR-03, CR-04]
status: fixed-awaiting-re-review
completed: 2026-10-06
commits:
  red: f8fde94
  green: 8f56372
files:
  - frontend/src/components/AccountPanel.tsx
  - frontend/src/app/(workspace)/datasets/page.tsx
  - frontend/tests/e2e/accounts.spec.ts
  - frontend/tests/e2e/datasets.spec.ts
---

# Phase 1 UI review fixes

The three reviewed UI defects are fixed with browser regressions. The orchestrator owns final review disposition, shared planning updates and the documentation commit.

## CR-02: Reset validation no longer blocks metadata-only saves

The reset button temporarily requires the password only while checking its native validity, then restores the field's previous `required` value in `finally`. Account creation retains its required password. Existing-account metadata edits can proceed after an empty reset attempt or a failed reset API request whose error handler clears the password. Metadata PATCH and password-reset POST remain distinct backend operations.

Two real-browser cases reproduce the empty reset and reset-503 paths, then successfully save the display name without supplying a temporary password. The 503 is injected only into reset delivery; the subsequent metadata PATCH reaches the real API and the account row updates.

## CR-03: Metadata save cannot dismiss a replacement dialog

MetadataPanel marks itself busy and prevents Escape while a save is in flight. A mounted-instance guard checks the continuation after the save and after the awaited list refresh, and suppresses state/error/close callbacks after unmount. An obsolete instance therefore cannot invoke its parent close callback against a newer panel.

The delayed-response tests fetch and commit the actual POST before withholding its browser delivery. One checks that Escape leaves the busy panel open, then allows normal completion and reopening. The other dispatches the existing access-change event to unmount the panel, opens a replacement with unsaved edits, and releases the old successful response. The replacement stays open with its edits; a later passive refresh displays the already committed dataset. No cancellation or rollback of an already committed request is claimed.

## CR-04: Authorized passive refresh preserves pending detail

Dataset selection/pending identity is tracked separately from list-request and detail-request generations. A successful passive refresh does not invalidate a pending detail when its selected ID remains in the refreshed list. Selection changes, page changes/cleanup, closing detail, a missing selected ID, failed scope refresh or an access-rejection event invalidate it. A late response also must match the still-selected ID before rendering.

Controlled browser delivery covers both list-before-detail and detail-before-list orders with real authorized responses. Additional controls verify that an old successful detail stays suppressed after a refreshed list excludes its ID or a list request returns 403. Those two controls inject the client scope/error response; the existing two-browser grant/revocation scenario continues to verify actual backend permission changes and stale-content clearing.

## RED and GREEN evidence

- **RED `f8fde94`:** unchanged production image, six new targeted scenarios; **5 failed / 1 passed in 39.8s**. The failures were the two reset recovery cases, busy Escape dismissal, obsolete completion losing replacement edits, and authorized list-first detail suppression. The detail-first ordering control passed. No collection, syntax, import or fixture failure was the reason for RED.
- **GREEN `8f56372`:** targeted regressions expanded with the two scope/error safety controls; **8 passed in 15.6s**.
- **Final full frontend:** **15 passed in 36.1s**, including existing account creation/password rotation/reset, narrow navigation/panel focus, actual live grants/revocation, UI smoke, passive polling/expiry, authentication tracer and safe configuration. Tests ran sequentially against isolated `postgres-test/rag_test`.
- **Production build:** Next.js build passed, compiled in 3.7s and completed TypeScript in 2.8s. No layout/CSS changes were made.
- **Typecheck/lint:** separate `npm run typecheck` and `npm run lint` passed with the latest test sources.
- **Scoped diff check:** passed. Backend/support code, shared planning documents and the runner-fix files were not edited by this executor. No backend suite was rerun for these frontend-only changes. No AI calls, dependency installation, operational data deletion or new product capability was introduced.

The test browser image and fixed production Next image were built with the locked existing dependencies. Latest test files were mounted read-only for verification so the added scope/error controls were included without claiming an older copied test set was current:

```text
docker compose build next-test frontend-test
docker compose run --rm -v D:/KhacNghia/RAG/frontend/tests:/app/frontend/tests:ro frontend-test npm run test:e2e -- accounts.spec.ts datasets.spec.ts --grep "review CR-"
docker compose run --rm -v D:/KhacNghia/RAG/frontend/tests:/app/frontend/tests:ro frontend-test npm run test:e2e
docker compose run --rm --no-deps -v D:/KhacNghia/RAG/frontend/tests:/app/frontend/tests:ro next-test npm run typecheck
docker compose run --rm --no-deps -v D:/KhacNghia/RAG/frontend/tests:/app/frontend/tests:ro next-test npm run lint
```

## Self-check: PASSED

The four source/test files and this record exist on disk. RED `f8fde94` and GREEN `8f56372` resolve in Git in order. Final scoped diff check passes. The fixes introduce no known stub or skipped/unrun required check; root-owned documentation commit and re-review follow.

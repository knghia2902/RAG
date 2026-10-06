---
phase: 01-local-workspace-and-access-control
reviewed: 2026-10-06T06:02:29Z
depth: standard
reviewed_head: 0362b766a9029ff5fa18251e3d99ab37cd4c190b
diff_base: 41ba345069d74855575727a5c2cc7636fb6820d2
files_reviewed: 83
files_reviewed_list:
  - ".env.example"
  - ".gitignore"
  - "backend/.dockerignore"
  - "backend/alembic.ini"
  - "backend/alembic/env.py"
  - "backend/alembic/versions/0001_access_control.py"
  - "backend/app/api/auth.py"
  - "backend/app/api/datasets.py"
  - "backend/app/api/dependencies.py"
  - "backend/app/api/errors.py"
  - "backend/app/api/health.py"
  - "backend/app/api/schemas.py"
  - "backend/app/api/status.py"
  - "backend/app/api/users.py"
  - "backend/app/auth/accounts.py"
  - "backend/app/auth/csrf.py"
  - "backend/app/auth/passwords.py"
  - "backend/app/auth/policy.py"
  - "backend/app/auth/rate_limit.py"
  - "backend/app/auth/sessions.py"
  - "backend/app/config.py"
  - "backend/app/database/datasets.py"
  - "backend/app/database/models.py"
  - "backend/app/database/session.py"
  - "backend/app/llm/__init__.py"
  - "backend/app/llm/contracts.py"
  - "backend/app/main.py"
  - "backend/app/modules/log_analysis/__init__.py"
  - "backend/app/modules/reports/__init__.py"
  - "backend/app/modules/tickets/__init__.py"
  - "backend/app/rag/__init__.py"
  - "backend/app/rag/contracts.py"
  - "backend/Dockerfile"
  - "backend/pyproject.toml"
  - "backend/requirements.lock"
  - "backend/scripts/bootstrap_admin.py"
  - "backend/scripts/seed_demo.py"
  - "backend/tests/__init__.py"
  - "backend/tests/conftest.py"
  - "backend/tests/integration/test_acl.py"
  - "backend/tests/integration/test_admin_users.py"
  - "backend/tests/integration/test_auth.py"
  - "backend/tests/integration/test_bootstrap_seed.py"
  - "backend/tests/integration/test_migrations.py"
  - "backend/tests/integration/test_startup.py"
  - "backend/tests/support.py"
  - "backend/tests/unit/test_module_boundaries.py"
  - "backend/tests/unit/test_policy.py"
  - "backend/tests/unit/test_session_clock.py"
  - "data/sample/.gitkeep"
  - "data/uploads/.gitkeep"
  - "docker-compose.yml"
  - "docs/local-development.md"
  - "docs/module-boundaries.md"
  - "docs/security-contracts.md"
  - "frontend/.dockerignore"
  - "frontend/Dockerfile"
  - "frontend/eslint.config.mjs"
  - "frontend/next.config.ts"
  - "frontend/next-env.d.ts"
  - "frontend/package.json"
  - "frontend/playwright.config.ts"
  - "frontend/src/app/(workspace)/accounts/page.tsx"
  - "frontend/src/app/(workspace)/configuration/page.tsx"
  - "frontend/src/app/(workspace)/datasets/page.tsx"
  - "frontend/src/app/(workspace)/layout.tsx"
  - "frontend/src/app/change-password/page.tsx"
  - "frontend/src/app/globals.css"
  - "frontend/src/app/layout.tsx"
  - "frontend/src/app/login/page.tsx"
  - "frontend/src/components/AccountPanel.tsx"
  - "frontend/src/components/DatasetGrantPanel.tsx"
  - "frontend/src/components/Sidebar.tsx"
  - "frontend/src/hooks/use-session.ts"
  - "frontend/src/lib/api.ts"
  - "frontend/src/lib/contracts.ts"
  - "frontend/tests/e2e/accounts.spec.ts"
  - "frontend/tests/e2e/datasets.spec.ts"
  - "frontend/tests/e2e/phase1.spec.ts"
  - "frontend/tests/e2e/status.spec.ts"
  - "frontend/tsconfig.json"
  - "storage/.gitkeep"
  - "tools/verify-local.ps1"
findings:
  critical: 4
  warning: 1
  info: 0
  total: 5
status: issues_found
---

# Phase 1: Code Review Report

**Reviewed:** 2026-10-06T06:02:29Z
**Depth:** standard
**Files Reviewed:** 83
**Status:** issues_found

## Summary

Reviewed the explicit scope against Git changes from `41ba345069d74855575727a5c2cc7636fb6820d2` through `0362b766a9029ff5fa18251e3d99ab37cd4c190b`, the five plan SUMMARY frontmatters, project instructions, and called auth/database/UI helpers. No project-local skills or configured reviewer skill mapping were present. No structural pre-pass was supplied.

Five defects remain: one acceptance-runner data-loss risk, three incorrect browser behaviors, and one cleanup robustness failure. BLOCKER classification follows the review contract for incorrect behavior or data-loss risk; it does not imply the three browser defects have the same impact as volume deletion. The existing 76 backend / 7 browser passes and operational acceptance pass were supplied by the orchestrator; this review does not claim to have rerun them or to have executed the destructive volume scenario. Reproduction sequences below follow the actual control flow and identify missing cases in those suites.

Future ingestion, retrieval, report/PDF endpoints and provider implementations are intentionally outside Phase 1. Their absence is not a finding. No source files were modified and no commits were made.

## Narrative Findings (AI reviewer)

## Critical Issues

### CR-01: Existing unlabelled volumes can be mounted and deleted by the acceptance runner

**Severity:** BLOCKER
**File:** `D:/KhacNghia/RAG/tools/verify-local.ps1:43-46`
**Related lines:** `69`, `75-78`, `100-101`, `135-138`
**Issue:** The preflight only looks for volumes with `com.docker.compose.project=$TestProject`. The generated configuration nevertheless assigns predictable explicit names such as `rag-phase1-acceptance_postgres-data` and `rag-phase1-acceptance_postgres-test-data`. A volume with one of those names and no project label passes the preflight. Compose can reuse that existing volume, and the unconditional `down --volumes` cleanup targets the volumes declared in the generated configuration, without verifying ownership. An existing operational database in the first name can fail the fresh-database check and then be deleted in `finally`. An existing test database in the second name can be cleared by the selected tests before cleanup. The comment that cleanup removes only freshly created labelled resources is not enforced by the code.

**Reproduction:** In a disposable Docker environment, pre-create an unlabelled volume named `<TestProject>_postgres-data`, put a sentinel file in it, and run the acceptance script with that TestProject. The label query is empty although the exact configured volume name already exists. The first database start mounts that volume; cleanup subsequently requests its deletion. Do not perform this reproduction against an operator volume. Docker documents that Compose [reuses existing named volumes and uses an explicit name as-is](https://docs.docker.com/reference/compose-file/volumes/).

**Fix:** After resolving the generated configuration, check existence of every actual volume and network name, regardless of labels, and reject collisions before any container starts. Prefer names containing a unique run identifier. Record the resources actually created for this run and verify a run-specific ownership label before destructive cleanup; reject concurrent reuse of the same project. Add a disposable sentinel-volume regression that proves a preexisting unlabelled resource is rejected and preserved.

### CR-02: A failed reset attempt makes a temporary password mandatory for ordinary account edits

**Severity:** BLOCKER
**File:** `D:/KhacNghia/RAG/frontend/src/components/AccountPanel.tsx:13`
**Related lines:** `8-12`
**Issue:** The reset button imperatively sets `field.required=true` on the shared form's temporary-password field and never restores it. On an existing account, clicking reset with an empty password leaves the dialog open with that field required. A later attempt to save only the display name, role or active flag is blocked by native form validation. The same problem follows a reset API failure: the catch clears the password, while `required` stays true. Those metadata changes do not require a password and are otherwise supported by the backend.

**Reproduction:** Open an existing account, leave the temporary password empty, click reset, change the display name, then click save account. No PATCH is sent; the password field reports a required-value error. Alternatively, return a 503 for reset and retry a metadata-only edit after the catch clears the field.

**Fix:** Validate the reset input without permanently mutating the metadata form's required state. Use a separate reset form, or restore the prior `required` value in `finally` around reset validation. Keep it required for account creation only. Cover both invalid reset input and a failed reset request followed by a successful metadata-only save.

### CR-03: Completing a dismissed metadata save closes a newer dialog and discards its edits

**Severity:** BLOCKER
**File:** `D:/KhacNghia/RAG/frontend/src/app/(workspace)/datasets/page.tsx:12`
**Related lines:** `9-11`, `16`, `22`
**Issue:** Unlike the account and grant dialogs, MetadataPanel permits Escape cancellation during an in-flight save: `onCancel={onClose}` has no busy guard. The asynchronous submit then continues after unmount and calls the parent `onClose` after `onSaved`. That parent callback unconditionally sets the current panel to undefined. If the Admin opens another create/edit dialog before the old request completes, the old completion closes the new dialog and discards the new unsaved form. The original mutation can also commit after the operator has dismissed its UI, leaving its result unclear.

**Reproduction:** Delay a metadata POST/PATCH response, submit the form, press Escape, open a second metadata dialog and enter a different name. Release the first response. Its eventual `onClose` removes the second dialog. This follows the real parent callback at line 22; unmounting does not cancel the HTTP request or the submit continuation.

**Fix:** Prevent Escape while busy and mark the dialog busy, matching the other mutation dialogs. Also invalidate the submit continuation on unmount or use a panel identity so an old completion cannot close a newer instance. Do not claim cancellation rolls back a request that may already have committed. Add a delayed-request browser regression for Escape and reopening.

### CR-04: A passive list response silently cancels a valid dataset detail selection

**Severity:** BLOCKER
**File:** `D:/KhacNghia/RAG/frontend/src/app/(workspace)/datasets/page.tsx:18`
**Related lines:** `16-20`, `22`; `D:/KhacNghia/RAG/frontend/src/hooks/use-session.ts:31-39`
**Issue:** Every successful list refresh increments `detailSequence.current`, even when the selected dataset remains authorized and the list has not changed. A detail request captures that same sequence and only displays its result if the sequence is unchanged. A five-second passive refresh that finishes between the click and the detail response therefore invalidates the user's request. With no existing detail, `setDetail(old => ...)` preserves null, so the user gets no detail and no error despite a successful authorized GET. This is a request-ordering defect, independent of grant revocation.

**Reproduction:** Hold a successful `/datasets` polling response, click Xem for a currently listed dataset and hold the detail response. Release the list response first, then the successful detail response. The refresh increments the detail sequence; the click continuation fails its equality check and never sets the detail. The existing browser test only checks the ordinary response order.

**Fix:** Track the selected/pending dataset ID separately from the list-request generation. Keep a pending detail request valid when a fresh authorized list still includes that ID. Invalidate it when selection changes, the dataset leaves the authorized scope, the page changes, or an access-rejection event arrives. Add a browser regression that controls the two response orders while also preserving the existing revocation-clearing behavior.

## Warnings

### WR-01: Docker cleanup failure skips environment restoration and temporary-secret deletion

**Severity:** WARNING
**File:** `D:/KhacNghia/RAG/tools/verify-local.ps1:135-142`
**Related lines:** `15`, `17-23`, `37-38`, `61-73`
**Issue:** The first action in `finally` is `Compose down`, whose Docker wrapper throws on any nonzero exit. If Docker becomes unavailable or teardown fails, that throw exits the finally block before restoring POSTGRES_PASSWORD/OPENAI_API_KEY/APP_ORIGIN or deleting the temporary files. The generated compose.json contains the ephemeral database credential. Invoking this script from the current PowerShell process also leaves that process's environment overwritten. An ordinary failed cleanup thus defeats the cleanup steps that do not require Docker and can mask the original acceptance failure.

**Reproduction:** Make the Docker wrapper throw for the cleanup down call after `$owned=true`. Lines 140-142 are never reached; environment values and compose.json remain. No real Docker outage is needed to reproduce this control-flow case with a mocked wrapper.

**Fix:** Put Docker teardown in its own try/catch and put environment restoration and temporary-file cleanup in a nested finally that always executes. Preserve/report the original acceptance failure and any teardown failure separately, returning nonzero if either fails. Ensure each temporary-file cleanup is independently attempted even if another removal fails. Add a mocked-cleanup failure check proving restoration and secret-file deletion still occur.

---

_Reviewed: 2026-10-06T06:02:29Z_
_Reviewer: gsd-code-reviewer_
_Depth: standard_

---
phase: 01-local-workspace-and-access-control
audited: 2026-10-06
baseline: abstract-six-pillar-standards
status: complete
source_head: 17b2c87
review_head: 699711b
overall_score: 16
maximum_score: 24
pillar_scores:
  copywriting: 3
  visuals: 3
  color: 3
  typography: 2
  spacing: 3
  experience_design: 2
blocker_count: 0
warning_count: 10
priority_fix_count: 3
minor_recommendation_count: 7
needs_human_review: false
screenshots:
  fresh_capture: false
  existing_inspected: true
  provenance: phase-01-05-automated-browser-acceptance
  desktop: frontend/test-results/phase1-desktop.png
  narrow_panel: frontend/test-results/phase1-narrow.png
  narrow_workspace: frontend/test-results/phase1-narrow-workspace.png
registry_audit: not-applicable-no-components-json
---

# Phase 1 — UI Review

**Audited:** 2026-10-06  
**Baseline:** Abstract six-pillar standards, constrained by `01-CONTEXT.md` D-10–D-13 and the five executed plans. No UI-SPEC.md exists.  
**Screenshots:** Existing actual acceptance screenshots inspected; no fresh capture. Read-only HTTP probes found no server at localhost:3000, 5173 or 8080. The screenshot gitignore gate was created centrally and verified before any potential new capture; none was needed.

Audit applies to Vietnamese enterprise Admin/Technician foundation: login, temporary-password change, accounts, dataset metadata/grants and configuration status. Locked sidebar/table/right-panel layout is respected. Future RAG, analysis and reporting navigation is intentionally absent and is not a defect. No brand, exact breakpoint, token scale or 60/30/10 distribution was approved; this review does not invent such a contract.

Evidence combines current source inspection with 1280×720 desktop and 390×844 narrow acceptance images. Images predate subsequent request-state fixes, which did not change layout. Current interaction regression evidence is the orchestrator's latest 15 passing E2E scenarios (36.1s), 76 backend tests and passing typecheck/lint/build; this auditor read the scenarios but did not rerun them. The 1213ms focused smoke is previously recorded warm automated evidence. No live MCP interaction, human approval, tablet/375px capture or remote-LAN validation is claimed.

## Pillar Scores

| Pillar | Score | Key Finding |
|--------|-------|-------------|
| 1. Copywriting | 3/4 | Useful Vietnamese actions and no-grant guidance; account creation omits credential rules before validation. |
| 2. Visuals | 3/4 | Clear page/table/panel hierarchy; active navigation is semantic only. |
| 3. Color | 3/4 | Restrained neutral surfaces; every button uses identical primary treatment. |
| 4. Typography | 2/4 | Seven explicit size values and three weights; textarea misses inherited UI font. |
| 5. Spacing | 3/4 | Tables contain narrow overflow; metadata textarea and adjacent detail cards lack shared spacing. |
| 6. Experience Design | 2/4 | Strong authorization/race/keyboard evidence; failed and initial-load states remain incomplete. |

**Overall: 16/24.** Scores are independently graded; passing automated flows do not raise visual scores. No observed defect warrants BLOCKER classification. All ten findings below are WARNING recommendations.

## Top 3 Priority Fixes

1. **Separate account error from loading and provide retry** — a failed request currently announces both failure and ongoing loading, leaving the table unavailable — introduce explicit loading/error state, render mutually exclusive states and a `Thử lại` action calling the authoritative account refresh.
2. **Complete grant-panel initial loading/empty/error states** — an empty technician selector looks identical while data is loading, after a failed request, or when no technicians exist — expose list-loading status, an actionable no-technician message and list/grant retry actions; clear pending status after failure.
3. **Preview disruptive account/grant changes before commit** — resetting a password, disabling/demoting another account or removing grants can interrupt another technician's work immediately — display affected account and change summary, explain session/access effects, and confirm these specific changes before sending existing mutations. Ordinary metadata saves need no extra confirmation.

## Detailed Findings

### Pillar 1: Copywriting (3/4)

**WARNING UI-01 — Credential rules appear too late.** `frontend/src/components/AccountPanel.tsx:13` sets username 3–64 characters and temporary password 15–128 characters, but visible help describes only forced change. Username syntax/immutability and password length are not explained before entry. Add associated help text for username syntax and temporary-password length; on edit explain that username cannot change. `change-password/page.tsx:8` already communicates password length and provides a useful reference pattern.

Positive evidence: action labels name their object (`Tạo tài khoản`, `Lưu Dataset`, `Lưu quyền`); dataset empty states tell Admin to create a dataset and Technician to contact Admin (`datasets/page.tsx:22`). `configuration/page.tsx:23` accurately distinguishes configured AI from provider connectivity. Vietnamese language and technical Dataset/API vocabulary follow D-12. Generic transport fallback remains safe; no unsupported AI capability is advertised.

### Pillar 2: Visuals (3/4)

**WARNING UI-02 — Current sidebar item is visually indistinguishable.** `Sidebar.tsx:9` supplies `aria-current="page"`, but `globals.css:1–2` has no selector styling it. The desktop and narrow workspace images show all three links with identical color/weight/background. Add a visible selected-link background/border or weight using `[aria-current="page"]`, retaining the existing semantic attribute and layout.

Positive evidence: desktop has one clear page heading, primary create control, count and aligned table; right panel has labelled fields and readable controls. Narrow layout keeps navigation and confines the 640px table to the card. Text buttons do not require invented icon tooltips; row buttons already have contextual accessible names.

### Pillar 3: Color (3/4)

**WARNING UI-03 — Secondary and disruptive actions compete with primary actions.** One global `button` rule (`globals.css:1`) paints create/save, close, pagination, logout and reset identically with `#075b79`. The inspected panel visibly gives `Đóng` the same emphasis as `Lưu tài khoản`; desktop row edit/pagination repeat the same fill. Add neutral secondary styles for close/pagination/row actions and a distinct warning treatment for reset; reserve filled primary for the main action within each region.

CSS scan finds 11 unique hexadecimal colors plus one rgba backdrop, concentrated in the shared stylesheet, and zero Tailwind `text-primary`/`bg-primary`/`border-primary` classes. This is plain CSS, so absence of Tailwind is not a failure. Neutral canvas/white cards, dark sidebar, teal actions, red errors and amber keyboard focus form a coherent palette. No unsupported numerical 60/30/10 violation or contrast failure is asserted from eyeballing the images. Extracting semantic CSS variables would make the proposed button variants easier to maintain.

### Pillar 4: Typography (2/4)

**WARNING UI-04 — Small typography scale is unnecessarily fragmented.** `globals.css:1–2` explicitly declares 12, 13, 16, 19, 20, 21 and 28px (seven values) and normal/600/700 weights, before browser defaults such as `small`. Brand switches 21→19px while panel heading is 20px. Consolidate to a documented small scale, for example 13/16/20/28px and regular/semibold; apply it consistently to brand, headings, labels and metadata. This is an abstract-standard recommendation, not a claimed UI-SPEC violation.

**WARNING UI-05 — Metadata textarea does not inherit the interface font.** `datasets/page.tsx:12` renders `<textarea>` while `globals.css:1–2` assigns inherited font only to button/input/select. The description control therefore retains browser-specific textarea typography while other fields inherit Arial. Add textarea to the shared font rule. This finding is code-derived; the existing images do not depict that panel.

### Pillar 5: Spacing (3/4)

**WARNING UI-06 — Metadata description control lacks field sizing and separation.** `datasets/page.tsx:12` renders the textarea with no class/style; shared CSS gives width, padding, margins and border treatment to inputs/selects only. Add full available width, shared padding/border, a usable minimum height and a consistent bottom gap before actions. Preserve resizable multiline entry.

**WARNING UI-07 — Dataset detail card touches the list card.** `datasets/page.tsx:22` appends two `.card` sections directly; `.card` has padding/border but no outer gap (`globals.css:1–2`). Add a 16–24px gap through a dataset section stack or a scoped adjacent-card rule. Existing screenshots do not show the open detail; evidence is the JSX/CSS relationship.

Spacing scan shows shared 16/24/32/40px major regions but also 6/10/11/18/26/28px values and repeated inline panel padding of 28px in all three dialogs. No locked scale exists, so these values alone are not defects. The two mobile `.main` declarations (20px then 16px) are redundant but final cascade is deterministic. Narrow overflow handling is a demonstrated strength; do not replace the required table layout to fix spacing.

### Pillar 6: Experience Design (2/4)

**WARNING UI-08 — Account failure remains labelled loading and has no retry.** `accounts/page.tsx:10–11` sets data to null on failure; line 13 independently renders the error and `!data` loading status. A failed initial request therefore continues to announce `Đang tải tài khoản…`; recovery requires navigation/reload. Successful page-change loading also does not explicitly reset error. Use distinct loading/error/data states and inline retry. Dataset polling automatically retries list requests, but its error view at `datasets/page.tsx:22` also lacks an immediate retry action; make recovery consistent without weakening access-state clearing.

**WARNING UI-09 — Grant list initialization and failed grant load are ambiguous.** `DatasetGrantPanel.tsx:8–12` starts users/datasets as empty arrays with no initial loading flag or no-technician guidance. `load` at line 14 sets committed to null; a failure leaves line 20 displaying `Đang tải quyền Dataset…` alongside the alert. Add explicit list/grant loading and failed states, explain how to create a technician if there are none, and provide retry for the corresponding request. Keep authoritative reconciliation after partial saves, which is already implemented and tested.

**WARNING UI-10 — Disruptive actions have no impact summary/confirmation.** `AccountPanel.tsx:8–13` directly resets password and saves role/active changes; `DatasetGrantPanel.tsx:15–18` directly sends DELETE for unchecked grants. Backend protection of the last/self Admin and current permissions is strong but does not prevent unintended disruption of another user. Show affected account/removed datasets and session/access consequences before applying these changes. This is an experience recommendation; automated tests show existing authorized operations complete successfully.

State coverage: login disables its submitting action and changes label; all mutation dialogs expose busy state and block close/Escape during saves; configuration has loading/error/retry; datasets have role-specific emptiness, live grant refresh and stale-response sequencing; grant save reconciles partial failures and announces success. The current E2E code explicitly covers keyboard wrap/Escape/opener focus for account/grant panels, narrow containment, forced password recovery, cache clearing on revocation, delayed metadata completion and dataset list/detail races. These established behaviors are not reopened as speculative defects. Global unexpected-render error recovery is not evidenced by an app `error.tsx`, but no crash was observed; it is not separately scored as a broken flow.

## Files Audited

- `AGENTS.md`, `.planning/PROJECT.md`, `.planning/config.json` and `01-CONTEXT.md`.
- All five `01-01` through `01-05` PLAN.md and SUMMARY.md pairs.
- `frontend/src/app/{layout.tsx,globals.css,login/page.tsx,change-password/page.tsx}`.
- `frontend/src/app/(workspace)/{layout.tsx,accounts/page.tsx,datasets/page.tsx,configuration/page.tsx}`.
- `frontend/src/components/{Sidebar.tsx,AccountPanel.tsx,DatasetGrantPanel.tsx}`.
- `frontend/src/lib/{api.ts,contracts.ts}` and `frontend/src/hooks/use-session.ts` (contracts inventoried; relevant DTO usage reviewed at consumers).
- `frontend/tests/e2e/{phase1.spec.ts,accounts.spec.ts,datasets.spec.ts,status.spec.ts}`.
- Three ignored acceptance screenshots listed in frontmatter; `.planning/ui-reviews/.gitignore` verified.

No `components.json` or UI-SPEC third-party registry contract exists; registry safety audit is not applicable. No subjective brand decision needs approval to establish these concrete findings. Human usability preference and unobserved viewports remain outside the claimed evidence.

The runtime exposes no local Read/Write tool; reads used the available PowerShell tool and this report was created with the available structured `apply_patch` file tool. No source or shared planning state was edited, and no commit was performed by this auditor.

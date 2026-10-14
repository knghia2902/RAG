---
phase: 06
slug: mvp-reliability-and-acceptance
status: approved
created: 2026-10-14
---

# Phase 06: MVP Reliability and Acceptance — UI Design Contract

## Scope & Intent
Phase 06 focuses strictly on reliability, security fencing, RAG ground truth evaluation, latency benchmarking, one-click walkthrough demo, and operational runbook documentation. No new frontend components or routes are introduced in this phase.

## Existing Frontend Surface Reused
1. **Authentication (`/login`)**: Login as Admin (`admin`) and Technician (`tech`).
2. **Datasets (`/datasets`)**: Verification of dataset ACL and visibility of sample sources.
3. **Chat & Knowledge Retrieval (`/chat`)**: Verification of prompt injection filtering and source citation links.
4. **Logistics Incidents (`/incidents`)**: Verification of order `DH001` analysis, timeline, and conflict indicators.
5. **On-Demand Reports (`/reports`)**: Verification of deterministic metrics, MTTR calculations, and PDF download.

## Acceptance Criteria for UI Verification
- The one-click demo script `backend/scripts/demo_walkthrough.py` seeds all required data and produces ready-to-use accounts so that operators can immediately log in and verify the entire Web → RAG → Analysis → PDF journey on existing UI.

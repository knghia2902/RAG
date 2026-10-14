---
phase: 4
slug: logistics-incident-and-ticket-analysis
status: draft
nyquist_compliant: true
wave_0_complete: false
created: 2026-10-14
---

# Phase 4 — Validation Strategy: Logistics Incident and Ticket Analysis

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|---|---|
| **Framework** | pytest 9.1.1 (Backend) / TypeScript + Next.js (Frontend) |
| **Config file** | `backend/pyproject.toml` / `frontend/package.json` |
| **Quick run command** | `py -3.12 -m pytest backend/tests/unit/test_ticket_validator.py backend/tests/unit/test_log_correlator.py backend/tests/unit/test_incident_reasoner.py -q` |
| **Full suite command** | `py -3.12 -m pytest backend/tests/ -q && npm --prefix frontend run build` |
| **Estimated runtime** | ~25 seconds |

---

## Sampling Rate

- **After every task commit:** Run quick unit test command
- **After every plan wave:** Run backend integration suite + frontend build
- **Before `/gsd-verify-work`:** Full test suite must be 100% green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---|---|---|---|---|---|---|---|---|---|
| 04-01-01 | 01 | 1 | INC-02 | T-04-01 | Kiểm tra schema JSON/CSV nghiêm ngặt, từ chối file rác với chi tiết dòng vi phạm | unit | `py -3.12 -m pytest backend/tests/unit/test_ticket_validator.py -q` | ❌ W0 | ⬜ pending |
| 04-01-02 | 01 | 1 | INC-02 | T-04-02 | Service import ticket và lưu trữ bản ghi ticket theo schema | unit | `py -3.12 -m pytest backend/tests/unit/test_ticket_service.py -q` | ❌ W0 | ⬜ pending |
| 04-02-01 | 02 | 2 | INC-01 | T-04-03 | Log Correlator engine đối soát theo `order_id` (DH001 vs DH010) và xâu chuỗi timestamp | unit | `py -3.12 -m pytest backend/tests/unit/test_log_correlator.py -q` | ❌ W0 | ⬜ pending |
| 04-02-02 | 02 | 2 | INC-01, INC-04 | T-04-04 | Phát hiện điểm gãy đồng bộ WMS-TMS và trích xuất sự kiện timeline đa hệ thống | unit | `py -3.12 -m pytest backend/tests/unit/test_log_correlator.py -q` | ❌ W0 | ⬜ pending |
| 04-03-01 | 03 | 3 | INC-03, INC-04 | T-04-05 | Phân loại nhóm lỗi, hệ thống, mức ưu tiên và tìm kiếm SOP/tiền lệ tương tự | unit | `py -3.12 -m pytest backend/tests/unit/test_incident_reasoner.py -q` | ❌ W0 | ⬜ pending |
| 04-03-02 | 03 | 3 | INC-05 | T-04-06 | Sinh giả thuyết nguyên nhân gốc rễ, cảnh báo thiếu dữ liệu và các bước xử lý đề xuất | unit | `py -3.12 -m pytest backend/tests/unit/test_incident_reasoner.py -q` | ❌ W0 | ⬜ pending |
| 04-04-01 | 04 | 4 | INC-01, INC-02 | T-04-07 | Endpoints `/api/v1/incidents/analyze`, `/upload-ticket` và `/history` | integration | `py -3.12 -m pytest backend/tests/integration/test_incident_api.py -q` | ❌ W0 | ⬜ pending |
| 04-04-02 | 04 | 4 | INC-01, AUTH-04 | T-04-08 | Live Scope Recheck chặn 403 khi thu hồi quyền dataset của log sự cố | integration | `py -3.12 -m pytest backend/tests/integration/test_incident_scope_recheck.py -q` | ❌ W0 | ⬜ pending |
| 04-05-01 | 05 | 5 | INC-01, INC-03, INC-04, INC-05 | T-04-09 | Giao diện Dashboard 4 khối, timeline trực quan phân màu hệ thống và drawer xem log | e2e / build | `npm --prefix frontend run build` | ❌ W0 | ⬜ pending |
| 04-05-02 | 05 | 5 | EVAL-01 | T-04-10 | Bộ dữ liệu mẫu WMS/TMS/API, ticket, incident, SOP kiểm chứng end-to-end DH001 | integration | `py -3.12 -m pytest backend/tests/integration/test_logistics_eval_dh001.py -q` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `backend/tests/unit/test_ticket_validator.py` — kiểm thử schema validation cho tệp JSON và CSV.
- [ ] `backend/tests/unit/test_log_correlator.py` — kiểm thử xâu chuỗi log WMS-API-TMS và phát hiện điểm đứt gãy.
- [ ] `backend/tests/unit/test_incident_reasoner.py` — kiểm thử reasoning phân loại lỗi và sinh giả thuyết nguyên nhân.
- [ ] `backend/tests/integration/test_incident_api.py` — kiểm thử API router incidents và quản lý lịch sử phân tích.

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|---|---|---|---|
| Trải nghiệm trực quan Timeline phân màu | INC-01 | Cảm nhận thị giác về độ tương phản nhãn WMS/API/TMS và viền đỏ điểm gãy đồng bộ | Mở `/incidents`, nhập `DH001`, kiểm tra giao diện hiển thị đúng 4 khối và timeline có viền đỏ nổi bật |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 30s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** approved 2026-10-14

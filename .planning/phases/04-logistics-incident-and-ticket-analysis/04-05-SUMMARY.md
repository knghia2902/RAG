---
phase: 04-logistics-incident-and-ticket-analysis
plan: "05"
subsystem: incident-dashboard-ui-and-eval01-acceptance
tags: [incidents-ui, timeline-component, nextjs, logistics-fixtures, eval-01, e2e-acceptance, turbopack]
requires: [04-04]
provides:
  - Multi-system event timeline component with system color badges and red failure highlighting in frontend/src/components/Timeline.tsx
  - Incident analysis workspace with dual input (Quick Form + Ticket Upload) and 4-block Dashboard in frontend/src/app/(workspace)/incidents/page.tsx
  - Sidebar navigation entry "Phân tích sự cố" (/incidents) for Admin and Technician in frontend/src/components/Sidebar.tsx
  - Concrete logistics sample fixtures (WMS logs, API Gateway logs, TMS logs, SOP-LOG-01, and tickets) in data/sample/logistics_incidents/
  - End-to-end acceptance test suite verifying EVAL-01 against ground truth metrics in backend/tests/integration/test_logistics_eval_dh001.py
affects: [05-incident-reporting-and-export]
tech-stack:
  added: []
  patterns: [4-block-incident-dashboard, multi-system-timeline, provenance-badges, dual-input-workspace, e2e-eval-suite]
key-files:
  created:
    - frontend/src/components/Timeline.tsx
    - frontend/src/app/(workspace)/incidents/page.tsx
    - data/sample/logistics_incidents/wms_songthan_orders.log
    - data/sample/logistics_incidents/api_gateway_access.log
    - data/sample/logistics_incidents/tms_dispatch.log
    - data/sample/logistics_incidents/SOP-LOG-01_Xu_Ly_Loi_Dong_Bo_WMS_TMS.txt
    - data/sample/logistics_incidents/sample_tickets.json
    - data/sample/logistics_incidents/sample_tickets.csv
    - backend/tests/integration/test_logistics_eval_dh001.py
  modified:
    - frontend/src/components/Sidebar.tsx
    - frontend/src/lib/contracts.ts
key-decisions:
  - "Trục thời gian sự kiện (Timeline) phân định trực quan mã màu theo từng hệ thống logistics: WMS (Xanh lam), API Gateway (Tím), TMS (Cam); làm nổi bật viền đỏ và biểu tượng cảnh báo tại điểm phát sinh lỗi đầu tiên (D-04)."
  - "Bố cục Dashboard 4 khối chuyên sâu theo quyết định D-03: Khối 1 (Tổng quan & Phân loại), Khối 2 (Trục thời gian đa hệ thống), Khối 3 (Giả thuyết nguyên nhân & Cảnh báo thiếu thông tin RAG-05), Khối 4 (Các bước xử lý theo SOP)."
  - "Bộ dữ liệu mẫu đa hệ thống tại data/sample/logistics_incidents/ cung cấp kịch bản chuẩn cho đơn hàng lỗi DH001 và đơn hàng đối chứng thành công DH010."
  - "Kiểm thử chấp nhận EVAL-01 (test_logistics_eval_dh001.py) xác thực tự động 6 chỉ tiêu: phân biệt tuyệt đối mã đơn hàng, chính xác nhóm lỗi và mức ưu tiên P1, phát hiện đúng điểm gãy 504, phân tách giả thuyết vs nguyên nhân xác nhận, cảnh báo thiếu log TMS, và dẫn chứng SOP-LOG-01."
requirements-completed: [INC-01, INC-03, INC-04, INC-05, EVAL-01]
actuals:
  tokens: 48000
  tasks: 3
  commits: 1
duration: 18min
completed: 2026-10-14
status: complete
---

# Phase 4 Plan 05: UI & EVAL-01 Acceptance Fixtures Summary

**Xây dựng giao diện Dashboard phân tích sự cố 4 khối tại `/incidents`, thành phần Trục dòng thời gian trực quan phân màu theo hệ thống (`Timeline.tsx`), tích hợp liên kết Sidebar, và tạo lập bộ dữ liệu mẫu chuẩn logistics (`data/sample/logistics_incidents/`) kèm kiểm thử chấp nhận E2E hoàn chỉnh theo yêu cầu EVAL-01, INC-01 đến INC-05.**

## Hoàn thành các nhiệm vụ

### 1. Multi-System Event Timeline Component (Task 04-05-01)
- Tạo `frontend/src/components/Timeline.tsx`:
  - Trục dọc kết nối sự kiện đa hệ thống WMS (Xanh lam), API Gateway (Tím), TMS (Cam), ERP/Inventory (Xanh nhạt).
  - Định dạng nhãn thời gian chuẩn Việt Nam `HH:mm:ss DD/MM/YYYY`.
  - Làm nổi bật viền đỏ đậm (`border-2 border-red-500 bg-red-50/60`), cờ cảnh báo và dòng chữ `*** ĐIỂM ĐỨT GÃY ĐỒNG BỘ PHÁT HIỆN TẠI ĐÂY ***` trên node sự kiện lỗi đầu tiên (`is_failure_point === true`).
  - Nút xem trích dẫn log gốc kèm số hiệu `#citation_id`.
  - Render an toàn chống XSS qua thẻ `<pre>` thuần túy, không dùng `dangerouslySetInnerHTML`.

### 2. Incident Workspace Page & Sidebar Integration (Task 04-05-02)
- Cập nhật `frontend/src/components/Sidebar.tsx` bổ sung liên kết `Phân tích sự cố` (`/incidents`) cho cả Admin và Kỹ thuật viên.
- Cập nhật `frontend/src/lib/contracts.ts` với đầy đủ các kiểu dữ liệu `TimelineEvent`, `IncidentClassification`, `RootCauseHypothesis`, `ActionStep`, `IncidentAnalysisDetail`, `IncidentHistoryItem`.
- Tạo màn hình `frontend/src/app/(workspace)/incidents/page.tsx`:
  - Form chuyển đổi 2 chế độ: Nhập nhanh Order ID và Tải tệp Ticket (JSON / CSV).
  - Bảng báo lỗi chi tiết theo từng dòng (HTTP 422) khi tệp ticket vi phạm cấu trúc schema.
  - Dashboard 4 khối hoàn chỉnh (Tổng quan, Trục thời gian, Giả thuyết & Cảnh báo thiếu dữ liệu RAG-05, Các bước xử lý theo SOP).
  - Modal xem chi tiết đoạn trích dẫn nguồn.
- Build Next.js thành công 100% với Turbopack (`npm run build`), trang `/incidents` sinh tĩnh ổn định.

### 3. Concrete Sample Logistics Fixtures & EVAL-01 Acceptance Suite (Task 04-05-03)
- Tạo lập bộ dữ liệu mẫu thực tế tại `data/sample/logistics_incidents/`:
  - `wms_songthan_orders.log`: Ghi nhận luồng đóng gói đơn hàng DH001, DH010, DH0011 tại Kho Sóng Thần.
  - `api_gateway_access.log`: Ghi nhận luồng chuyển tiếp đồng bộ và lỗi HTTP 504 Gateway Timeout cho DH001.
  - `tms_dispatch.log`: Ghi nhận luồng nhận lệnh của DH010 và khuyết hoàn toàn DH001.
  - `SOP-LOG-01_Xu_Ly_Loi_Dong_Bo_WMS_TMS.txt`: Quy trình thao tác chuẩn ứng cứu lỗi mất đồng bộ WMS-TMS.
  - `sample_tickets.json` & `sample_tickets.csv`: Tệp ticket mẫu cho các ca sự cố.
- Tạo kịch bản kiểm thử chấp nhận `backend/tests/integration/test_logistics_eval_dh001.py`:
  - `test_eval_dh001_incident_analysis_e2e`: Kiểm chứng toàn bộ 6 tiêu chí chấp nhận EVAL-01.
  - `test_eval_dh010_healthy_order_comparison`: Đối chứng đơn hàng thành công DH010 không có lỗi đồng bộ và không bị lẫn mã định danh.
- Toàn bộ 7/7 bài kiểm thử tích hợp Phase 4 đều đạt 100% PASSED.

---
phase: 05-on-demand-incident-reports-and-pdf
plan: "04"
subsystem: reports-ui-and-e2e-verification
tags: [reports-ui, nextjs, turbopack, pdf-preview, e2e-acceptance, eval-03]
requires: [05-03]
provides:
  - Sidebar navigation link for 'Báo cáo sự cố' (/reports) for admin and technician roles in frontend/src/components/Sidebar.tsx
  - TypeScript contracts matching all backend Report DTOs in frontend/src/lib/contracts.ts
  - Full two-tab Reports Workspace page and Preview Dashboard in frontend/src/app/(workspace)/reports/page.tsx
  - Comprehensive end-to-end acceptance test suite covering EVAL-03 in backend/tests/integration/test_reports_e2e_acceptance.py
affects: []
tech-stack:
  added: []
  patterns: [two-tab-workspace, kpi-dashboard, provenance-snapshot-modal, live-scope-403-handling, turbopack-build]
key-files:
  created:
    - frontend/src/app/(workspace)/reports/page.tsx
    - backend/tests/integration/test_reports_e2e_acceptance.py
  modified:
    - frontend/src/components/Sidebar.tsx
    - frontend/src/lib/contracts.ts
key-decisions:
  - "Bổ sung mục điều hướng 'Báo cáo sự cố' trên Sidebar cho cả quản trị viên và kỹ thuật viên."
  - "Xây dựng giao diện Workspace 2 tab trực quan trên Next.js: Tab 1 tạo báo cáo theo kỳ (Hôm nay, Tuần này, Tháng này, Tùy chọn) với bộ chọn dataset đa năng; Tab 2 liệt kê lịch sử báo cáo với tính năng xem trước và tải PDF."
  - "Dashboard xem trước hiển thị nổi bật 5 thẻ KPI cốt lõi, bảng phân bổ hệ thống và mức ưu tiên, bảng danh mục lỗi lặp lại (>= 2 lần) kèm đơn hàng bị ảnh hưởng, và nhận định vận hành của AI."
  - "Khi quyền truy cập dataset bị thu hồi, giao diện hiển thị cảnh báo lỗi 403 Forbidden nổi bật và đóng bản xem trước để ngăn ngừa rò rỉ thông tin (T-05-07)."
  - "Bộ kiểm thử E2E EVAL-03 xác thực 100% độ chính xác số liệu thống kê so với ground truth và kiểm soát biên kỳ/timezone."
requirements-completed: [REP-01, REP-02, REP-05, REP-06, EVAL-03]
actuals:
  tokens: 35000
  tasks: 3
  commits: 1
duration: 12min
completed: 2026-10-14
status: complete
---

# Phase 5 Plan 04: Report Workspace UI, PDF Preview & Integration Acceptance Summary

**Hoàn thiện giao diện Next.js App Router cho module Báo cáo sự cố (`/reports`), tích hợp các hợp đồng TypeScript, xây dựng dashboard xem trước kèm tải PDF tiếng Việt, và xác thực toàn diện chỉ tiêu nghiệm thu EVAL-03.**

## Hoàn thành các nhiệm vụ

### 1. Navigation & TypeScript Contracts Integration (Task 05-04-01)
- Cập nhật `frontend/src/components/Sidebar.tsx`: Bổ sung đường dẫn điều hướng `["/reports", "Báo cáo sự cố"]` cho cả hai vai trò `admin` và `technician`.
- Cập nhật `frontend/src/lib/contracts.ts`: Định nghĩa đầy đủ các interface TypeScript `PeriodType`, `ReportFilter`, `RecurringErrorItem`, `SystemDistribution`, `PriorityDistribution`, `ReportMetrics`, `ReportNarrative`, `ReportProvenanceSource`, `ReportDetail` và `ReportHistoryItem`.

### 2. Two-Tab Reports Workspace Page & Preview Dashboard (Task 05-04-02)
- Tạo `frontend/src/app/(workspace)/reports/page.tsx`:
  - Tab 1 "Tạo báo cáo mới": Bộ chọn kỳ nhanh (Hôm nay, Tuần này, Tháng này, Tùy chọn), bộ chọn phạm vi dataset được cấp quyền, và nút "Tạo báo cáo ngay".
  - Tab 2 "Lịch sử báo cáo": Bảng liệt kê các báo cáo đã tạo, thời điểm lập, số lượng sự cố/ticket, các nút thao tác "Xem trước" và "Tải PDF".
  - Thành phần Preview Dashboard:
    - 5 thẻ chỉ số KPI: Tổng sự cố, Ticket IT, Đang mở, Đã giải quyết, MTTR trung bình.
    - Bảng phân bổ theo Hệ thống (WMS, TMS, API Gateway) và Mức độ ưu tiên (P1, P2, P3, P4).
    - Bảng Lỗi lặp lại ($\ge 2$ lần) kèm danh sách mã đơn hàng bị ảnh hưởng.
    - Khối Nhận định AI: Tóm tắt điều hành, Phân tích nguyên nhân và Khuyến nghị SOP.
    - Modal tra cứu nguồn tham chiếu (Provenance Snapshot).
    - Nút tải trực tiếp tệp PDF tiếng Việt A4 chuẩn in ấn.
  - Xử lý lỗi bảo mật: Hiển thị banner cảnh báo đỏ nổi bật khi nhận phản hồi HTTP 403 Forbidden từ backend (do Live Scope Recheck), lập tức xóa trạng thái xem trước nhằm ngăn ngừa rò rỉ dữ liệu (T-05-07).
- Biên dịch Next.js với Turbopack (`npm --prefix frontend run build`) hoàn tất thành công trong 15.5s, tạo static route `/reports` không có lỗi.

### 3. End-to-End Acceptance Test Suite (EVAL-03) (Task 05-04-03)
- Tạo `backend/tests/integration/test_reports_e2e_acceptance.py`:
  - `test_eval03_report_metrics_match_ground_truth`: Nạp dữ liệu sự cố mẫu logistics, xác thực số lượng ticket và incident khớp 100% với ground truth; MTTR tính chính xác 30.0 phút chỉ từ các sự cố/ticket đã hoàn tất; lỗi lặp `API_GATEWAY: 504_GATEWAY_TIMEOUT` được gom nhóm chính xác ($\ge 2$ lần) cùng danh sách đơn DH001 và DH010.
  - `test_eval03_pdf_download_and_scope_recheck_e2e`: Xác thực tải file PDF tiếng Việt hợp lệ dung lượng > 1KB; thu hồi quyền dataset của kỹ thuật viên và kiểm tra các endpoint chi tiết và tải PDF lập tức nhận HTTP 403 Forbidden.
- Toàn bộ 7/7 bài kiểm thử E2E và tích hợp của EVAL-03 đều đạt 100% passed.

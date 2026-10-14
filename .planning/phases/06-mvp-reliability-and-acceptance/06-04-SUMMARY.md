---
phase: 06-mvp-reliability-and-acceptance
plan: "04"
subsystem: operations-and-documentation
tags: [demo, walkthrough, runbook, evaluation-report, docker, operations, reindexing, docs]
requires: [06-01, 06-02, 06-03]
provides:
  - One-click demo walkthrough script in backend/scripts/demo_walkthrough.py
  - Comprehensive operations runbook in docs/runbook.md
  - Quantitative technical evaluation report in docs/evaluation.md
  - Sample logistics incidents directory seeded into backend/data/sample/
affects: []
tech-stack:
  added: []
  patterns: [one-click-walkthrough, operations-runbook, technical-evaluation, zero-downtime-reindex]
key-files:
  created:
    - backend/scripts/demo_walkthrough.py
    - docs/runbook.md
    - docs/evaluation.md
  modified: []
key-decisions:
  - "Cung cấp script demo_walkthrough.py cho phép thiết lập và trải nghiệm trọn vẹn luồng Web -> RAG -> analysis -> PDF chỉ bằng 1 lệnh duy nhất (D-10, EVAL-02, EVAL-03)."
  - "Tài liệu hóa chi tiết kiến trúc Docker Compose, xử lý lỗi Celery worker crash và quy trình reindex vector bất biến zero-downtime (D-11, EVAL-02, EVAL-03)."
  - "Tổng hợp toàn bộ ma trận kiểm thử nghiệm thu kỹ thuật và đối chiếu Ground Truth vào docs/evaluation.md (D-07, EVAL-02, EVAL-03)."
requirements-completed: [EVAL-02, EVAL-03]
actuals:
  tasks: 3
  commits: 1
duration: 12min
completed: 2026-10-14
status: complete
---

# Phase 06 Plan 04: One-Click Demo Walkthrough Script, Operations Runbook & Evaluation Report Summary

**Hoàn tất toàn bộ công tác tài liệu hóa vận hành và công cụ nghiệm thu cho MVP Modular RAG IT & Logistics: cung cấp script demo tích hợp 1 lệnh `backend/scripts/demo_walkthrough.py`, xuất bản cẩm nang vận hành chi tiết `docs/runbook.md` và hoàn thiện báo cáo nghiệm thu kỹ thuật định lượng `docs/evaluation.md`.**

## Hoàn thành các nhiệm vụ

### 1. One-Click Demo Walkthrough Script (Task 06-04-01)
- Xây dựng `backend/scripts/demo_walkthrough.py` tự động:
  - Khởi tạo tài khoản `admin` (`Admin@123456`) và `tech` (`Tech@123456`).
  - Thiết lập dataset `[Demo] Logistics Operations` và cấp quyền truy cập cho Kỹ thuật viên.
  - Tải lên và đánh chỉ mục 5 tệp mẫu (`wms_songthan_orders.log`, `tms_dispatch.log`, `api_gateway_access.log`, `SOP-LOG-01_Xu_Ly_Loi_Dong_Bo_WMS_TMS.txt`, `sample_tickets.csv`).
  - Thực hiện phân tích sự cố mẫu cho đơn hàng `DH001` (liên kết timeline WMS, TMS, API Gateway và đề xuất SOP).
  - Tạo báo cáo sự cố kỳ tuần kèm tệp PDF in ấn.
  - In thông tin đăng nhập và hướng dẫn 3 bước trải nghiệm Web.
- Hỗ trợ cờ `--dry-run` kiểm tra kết nối CSDL và tính toàn vẹn của tệp mẫu mà không ghi đè dữ liệu.

### 2. Operations Runbook Documentation (Task 06-04-02)
- Xuất bản tài liệu `docs/runbook.md` gồm 7 phần toàn diện:
  - Kiến trúc microservices và sơ đồ Docker Compose (`postgres`, `rabbitmq`, `migrate`, `backend`, `worker`, `frontend`).
  - Hướng dẫn cài đặt, cấu hình biến môi trường `.env` và lệnh khởi động nhanh.
  - Quy trình vận hành, theo dõi log, chạy test và benchmark độ trễ định kỳ.
  - Hướng dẫn khắc phục sự cố (Troubleshooting): phục hồi sự cố Celery worker crash qua lease idempotency và rollback CSDL.
  - Quy trình Tái lập chỉ mục Vector không downtime (Zero-Downtime Reindexing) qua `index_version`.
  - Bảng công bố giới hạn vận hành thực tế đã kiểm chứng (5MB ticket, 50MB source, 30s timeout, concurrency=2).

### 3. Technical Evaluation Report (Task 06-04-03)
- Xuất bản tài liệu `docs/evaluation.md` ghi nhận:
  - Ma trận kiểm thử nghiệm thu với 14 ca kiểm thử chi tiết, 100% đạt chuẩn (**PASSED**).
  - Đối chiếu số liệu báo cáo với Ground Truth Fixtures (tính tất định 100% từ CSDL quan hệ).
  - Bảng đo đạc độ trễ p50/p95 định lượng (Ingestion: 0.71 ms, Retrieval: 4.36 ms, Reasoning: 0.14 ms, PDF: 430.56 ms).
  - Khẳng định MVP sẵn sàng bàn giao vận hành.

## Kết quả kiểm thử
- `python scripts/demo_walkthrough.py --dry-run`: **Thành công (exit code 0)**.
- Kiểm tra tệp tài liệu: `docs/runbook.md` và `docs/evaluation.md` tồn tại và đầy đủ nội dung.
- Toàn bộ 223 bài kiểm thử của dự án: **223/223 passed (100%)** trong 88 giây.

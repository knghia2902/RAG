---
status: complete
phase: 06-mvp-reliability-and-acceptance
source:
  - .planning/phases/06-mvp-reliability-and-acceptance/06-01-SUMMARY.md
  - .planning/phases/06-mvp-reliability-and-acceptance/06-02-SUMMARY.md
  - .planning/phases/06-mvp-reliability-and-acceptance/06-03-SUMMARY.md
  - .planning/phases/06-mvp-reliability-and-acceptance/06-04-SUMMARY.md
started: 2026-10-14T20:10:00+07:00
updated: 2026-10-15T08:26:30+07:00
---

## Current Test

[testing complete]

## Tests

### 1. Cold Start & System Readiness Smoke Test
expected: Toàn bộ container Docker Compose khởi động thành công, endpoint `/health/ready` trả về HTTP 200, giao diện Web tại `http://localhost:3000` tải mượt mà không lỗi.
result: pass

### 2. One-Click Demo Walkthrough Execution
expected: Chạy lệnh `docker compose exec -T backend python scripts/demo_walkthrough.py --dry-run` kiểm tra thành công 5/5 tệp dữ liệu mẫu chuẩn và kết nối CSDL trả về exit code 0. Khi chạy không có cờ `--dry-run`, script tự động khởi tạo tài khoản, nạp dataset, phân tích đơn hàng DH001, tạo báo cáo và xuất tệp PDF.
result: pass

### 3. Prompt Injection Neutralization & Secret Masking Egress
expected: Khi gửi mô tả sự cố hoặc payload ticket chứa câu lệnh tiêm nhiễm prompt injection (ví dụ: "IGNORE ALL PREVIOUS INSTRUCTIONS..."), hệ thống xử lý hoàn toàn như văn bản tĩnh (inert data), không rò rỉ system prompt. Đồng thời các bí mật (API Key, Bearer token, password, database URL) trong log trích đoạn được tự động làm mờ thành [REDACTED_SECRET].
result: pass

### 4. Live Scope Recheck & Access Revocation Fencing (AUTH-04, REP-06)
expected: Khi Kỹ thuật viên bị thu hồi quyền truy cập một dataset, hệ thống thực thi Live Scope Recheck tức thì: Kỹ thuật viên không thể xem chi tiết sự cố, xem báo cáo hay tải tệp PDF liên quan đến dataset đó và nhận mã lỗi HTTP 403 Forbidden. Lịch sử chat và tệp bị xóa (tombstone) cũng được cô lập triệt để.
result: pass

### 5. Ground Truth Disambiguation (DH001 vs DH010) & RAG-05 Missing Evidence Alerting
expected: Khi tra cứu hoặc phân tích mã đơn hàng DH001, hệ thống chỉ hiển thị đúng các sự kiện thuộc DH001, tuyệt đối không bị lẫn sang DH010 hay DH0011. Khi đơn hàng thiếu bằng chứng log quan trọng (ví dụ thiếu log TMS cho DH003), hệ thống phát cảnh báo thiếu bằng chứng rõ ràng và xếp nguyên nhân vào diện giả thuyết chưa xác nhận.
result: pass

### 6. Citation Support Rate & Source Locator Fidelity
expected: 100% nguyên nhân sự cố đã xác nhận đều có trích dẫn nguồn bằng chứng xác thực kèm vị trí chính xác (tên tệp, dòng/hàng/sự kiện). Tỷ lệ trích dẫn tổng thể đạt tối thiểu 75%.
result: pass

### 7. Operations Runbook & Technical Evaluation Documentation
expected: Tệp `docs/runbook.md` cung cấp cẩm nang vận hành 7 chương đầy đủ (kiến trúc microservices, khắc phục sự cố worker, quy trình reindex vector không downtime, bảng giới hạn 5MB/50MB/30s). Tệp `docs/evaluation.md` ghi nhận ma trận 14 ca kiểm thử nghiệm thu đạt chuẩn 100% và bảng đo độ trễ thực tế p50/p95.
result: pass

## Summary

total: 7
passed: 7
issues: 0
pending: 0
skipped: 0

## Gaps

[none yet]

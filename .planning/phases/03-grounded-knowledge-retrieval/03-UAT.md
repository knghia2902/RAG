---
status: complete
phase: 03-grounded-knowledge-retrieval
source:
  - .planning/phases/03-grounded-knowledge-retrieval/03-01-SUMMARY.md
  - .planning/phases/03-grounded-knowledge-retrieval/03-02-SUMMARY.md
  - .planning/phases/03-grounded-knowledge-retrieval/03-03-SUMMARY.md
  - .planning/phases/03-grounded-knowledge-retrieval/03-04-SUMMARY.md
  - .planning/phases/03-grounded-knowledge-retrieval/03-05-SUMMARY.md
started: 2026-10-09T16:59:00+07:00
updated: 2026-10-14T10:33:45+07:00
---

## Current Test

[testing complete]

## Tests

### 1. Cold Start Smoke Test
expected: Khởi động ứng dụng từ trạng thái ban đầu. Backend FastAPI và Frontend Next.js khởi động không lỗi, các endpoint cốt lõi (/health/ready, /api/v1/status, trang chủ) phản hồi dữ liệu thành công.
result: pass

### 2. Exact Identifier Disambiguation (DH001 vs DH010)
expected: Khi nhập câu hỏi tra cứu chứa mã đơn hàng như "Kiểm tra đơn hàng DH001", hệ thống định vị chính xác bản ghi chứa mã DH001 ở vị trí ưu tiên đầu tiên và không bị nhầm lẫn, trùng lặp hay thay thế bởi các mã tương tự như DH010 (RAG-02).
result: pass

### 3. Grounded Generation with Inline Citations & Uncertainty/Conflict Flags
expected: Câu trả lời của AI dựa trên các đoạn bằng chứng đã truy xuất, kèm thẻ trích dẫn đánh số [1], [2]. Mọi thẻ trích dẫn ảo (hallucinated) không có trong ngữ cảnh đều bị lọc bỏ. Nếu dữ liệu thiếu hoặc có mâu thuẫn giữa các nguồn, câu trả lời hiển thị rõ ràng banner cảnh báo trực quan màu vàng (RAG-01, RAG-04, RAG-05).
result: pass

### 4. Scope Filters for Targeted Retrieval
expected: Người dùng có thể mở thanh bộ lọc phạm vi trên giao diện /chat để thu hẹp tìm kiếm theo Dataset cụ thể, loại hồ sơ (Quy trình SOP, Nhật ký Log, Phiếu Ticket, Bảng vận hành) và khoảng thời gian (Từ ngày - Đến ngày) (RAG-03).
result: pass

### 5. Evidence Preview Panel & Live Scope Recheck
expected: Nhấp vào thẻ trích dẫn [1] mở ra Evidence Preview Panel bên phải hiển thị tên file nguồn, version v{n}, dataset và tọa độ provenance chính xác (Trang, Dòng, Sheet/Hàng, JSON Path). Khi quyền truy cập vào dataset bị thu hồi, việc mở xem lại trích dẫn hoặc tải tin nhắn cũ sẽ ngay lập tức bị từ chối với thông báo lỗi 403 an toàn (D-01, D-05, AUTH-04).
result: pass

### 6. Model Configuration Inspection
expected: Tài khoản Quản trị viên truy cập trang Cấu hình (/configuration) xem được thẻ "Mô hình AI & Index Vector (SYS-02)" hiển thị thông số Embedding Provider (model, dimension 1536, index version), LLM Generation Provider và trạng thái API key mà không để lộ secret key ra trình duyệt (SYS-02).
result: pass

## Summary

total: 6
passed: 6
issues: 0
pending: 0
skipped: 0
blocked: 0

## Gaps


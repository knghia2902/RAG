# Project Research Summary

**Project:** Logistics IT RAG
**Researched:** 2026-10-03
**Overall confidence:** MEDIUM — tài liệu chính thức đã đối chiếu; chưa cài đặt, benchmark hoặc kiểm chứng trên hệ thống thật.
**Execution:** Nghiên cứu thực hiện inline trong phiên chính; không chạy research subagents.

## Executive Summary

Đề xuất Web SPA + API Python, PostgreSQL lưu dữ liệu chuẩn và Qdrant làm vector index local. RAG dùng exact/lexical/dense retrieval cho log/SOP/ticket; LLM Provider tách riêng và embedding ưu tiên local. Đây là đề xuất để lập kế hoạch, chưa phải stack chốt hay bằng chứng MVP hoạt động.

Báo cáo cần phối hợp hai đường dữ liệu: truy vấn có cấu trúc tính metrics và RAG cung cấp bằng chứng giải thích. LLM viết nhận xét/đề xuất, không tự suy ra tổng số từ vài đoạn top-k. Nguồn trích dẫn cần định vị page/section/row/event và version, không chỉ tên file.

## Key Findings

### Stack

Baseline đề xuất: Python 3.12.15, FastAPI 0.142.2, React 19.3, PostgreSQL 18, Qdrant 1.19.1, Docling 2.132.0, ứng viên BGE-M3 local, WeasyPrint 70 và worker riêng. Exact frontend/support-package pins và model revision phải khóa ở bước triển khai. Xem [STACK.md](STACK.md) để biết nguồn, lựa chọn thay thế và compatibility gate.

### Features

Phạm vi đã chốt gồm quản lý dữ liệu, hỏi đáp, log/incident/ticket analysis và báo cáo PDF có nguồn. Đề xuất thêm job lifecycle, source versions, xử lý thiếu evidence, counting rules và eval fixtures. OCR, xác thực/phân quyền, scheduler, feedback và reranker cần scope rõ; chưa tự thêm vào v1. Xem [FEATURES.md](FEATURES.md).

### Architecture

Modular monolith + worker; PostgreSQL là canonical store, Qdrant là derived index. Reports lưu snapshot metrics và provenance. Domain services độc lập API routes/SDK để thêm MCP/Agent về sau. Xem [ARCHITECTURE.md](ARCHITECTURE.md).

### Critical Pitfalls

Nhầm mã đơn hàng khi dùng semantic-only; bịa root cause từ precedent; đếm thiếu/trùng và lệch timezone; citation không chứng minh claim; index cũ sau xóa/reindex; mất jobs; prompt injection và context chứa secret. Xem [PITFALLS.md](PITFALLS.md) để biết dấu hiệu và biện pháp kiểm chứng.

## Implications for Roadmap

Gợi ý 6 phase theo năng lực, chưa phải roadmap chính thức:

1. Foundation + vertical slice upload → hỏi đáp có nguồn.
2. Multi-format ingestion, canonical records và source lifecycle.
3. Exact/hybrid retrieval, evidence viewer và baseline eval.
4. Phân tích ticket/sự cố WMS–TMS end-to-end.
5. Báo cáo số liệu kiểm chứng + PDF.
6. Recovery, chất lượng, provider boundaries và đóng gói local.

Giữ fixture DH001 làm luồng xuyên suốt; có ground truth logs/tickets/SOP và metrics, thêm near-collision IDs, duplicate, missing evidence, timezone boundary và provider failure. Roadmapper cần map requirements và điều chỉnh phase theo scope đã duyệt, không copy nguyên cấu trúc này.

## Confidence Assessment

| Nội dung | Mức tin cậy | Giới hạn |
|---|---|---|
| Khả năng SQL/vector/parser/API/PDF | High | Tài liệu chính thức, chưa kiểm tra compatibility toàn stack |
| Kiến trúc phù hợp MVP | Medium | Suy luận từ yêu cầu, chưa biết máy đích/quy mô |
| Embedding tiếng Việt/log và reranking | Medium/Low | Model card không thay benchmark dữ liệu logistics |
| Chỉ tiêu hiệu năng/chất lượng | Chưa xác định | Không bịa latency/accuracy hay hardware capacity |

## Gaps to Address

- Xác thực: local một workspace hay tài khoản admin/kỹ thuật viên; mức phân quyền tài liệu.
- Support matrix: PDF text/DOCX/CSV/XLSX/TXT/JSONL trước hay cần PDF scan/DOC/XLS cũ.
- Ticket import schema, timeline/priority mapping và quy tắc liên kết incident.
- Báo cáo theo yêu cầu hay lập lịch; timezone và quy tắc tính kỳ/duration.
- Hardware, quy mô dữ liệu, LLM API provider và các chỉ tiêu nghiệm thu.
- Chốt Docker Compose/stack; quyết định nào có thể giao người triển khai chọn thì ghi rõ trong yêu cầu.

## Sources

Primary sources được liên kết chi tiết trong [STACK.md](STACK.md), [FEATURES.md](FEATURES.md), [ARCHITECTURE.md](ARCHITECTURE.md) và [PITFALLS.md](PITFALLS.md). Bối cảnh sản phẩm lấy từ [PROJECT.md](../PROJECT.md) và yêu cầu người dùng; không dùng thông tin sản phẩm cạnh tranh chưa kiểm chứng.

---
*Research completed: 2026-10-03. Ready for requirements scoping; initialization workflow remains in progress.*

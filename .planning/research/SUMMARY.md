# Project Research Summary

**Project:** Modular RAG cho IT & Logistics
**Researched:** 2026-10-03
**Overall confidence:** MEDIUM — tài liệu chính thức đã đối chiếu; chưa cài đặt, benchmark hoặc kiểm chứng trên hệ thống thật.
**Execution:** Nghiên cứu thực hiện inline trong phiên chính; không chạy research subagents.

## Executive Summary

Stack người dùng đã chốt: Next.js/TypeScript Web + Python/FastAPI + LangChain + PostgreSQL/pgvector local, OpenAI Embeddings và OpenAI generation API. RAG dùng exact/lexical/dense retrieval cho log/SOP/ticket. Embedding Provider và LLM Provider độc lập. Quyết định này thay đề xuất Qdrant/React-Vite/local embedding ban đầu; chưa có bằng chứng MVP hoạt động.

Báo cáo cần phối hợp hai đường dữ liệu: truy vấn có cấu trúc tính metrics và RAG cung cấp bằng chứng giải thích. LLM viết nhận xét/đề xuất, không tự suy ra tổng số từ vài đoạn top-k. Nguồn trích dẫn cần định vị page/section/row/event và version, không chỉ tên file.

## Key Findings

### Stack

Baseline nghiên cứu: Python 3.12, FastAPI, PostgreSQL 18 + pgvector 0.8.7, LangChain integrations, Next.js/TypeScript, Docling, WeasyPrint và worker từ backend image. Đề xuất embedding text-embedding-3-small/1536 chiều, model cụ thể vẫn là cấu hình cần chốt. Exact package pins phải khóa khi scaffold. Xem [STACK.md](STACK.md).

### Features

Phạm vi đã chốt: Admin/Kỹ thuật viên, quản lý dữ liệu các format PDF text/DOCX/TXT/LOG/JSON/JSONL/CSV/XLSX, hỏi đáp, log/incident/ticket analysis, báo cáo theo kỳ/custom theo yêu cầu và PDF có nguồn. Dataset ACL là baseline thiết kế đề xuất. OCR, scheduler, MCP và Agent để sau. Xem [FEATURES.md](FEATURES.md).

### Architecture

Modular monolith theo backend/app của người dùng + worker, PostgreSQL lưu canonical data và pgvector derived index. Report Service lưu snapshot metrics/provenance. Embedding gửi chunks/query tới API; generation chỉ gửi retrieved context. Các module và provider boundaries chuẩn bị cho MCP/Agent/local models. Xem [ARCHITECTURE.md](ARCHITECTURE.md).

### Critical Pitfalls

Nhầm mã đơn hàng khi dùng semantic-only; bịa root cause từ precedent; đếm thiếu/trùng và lệch timezone; citation không chứng minh claim; index cũ sau xóa/reindex; mất jobs; prompt injection và context chứa secret. Xem [PITFALLS.md](PITFALLS.md) để biết dấu hiệu và biện pháp kiểm chứng.

## Implications for Roadmap

Gợi ý 6 phase theo năng lực, chưa phải roadmap chính thức:

1. Docker/local foundation + Admin/Kỹ thuật viên và quyền dataset.
2. Multi-format ingestion, canonical records và source lifecycle trên Web.
3. LangChain/pgvector RAG + OpenAI providers + citations end-to-end.
4. Phân tích ticket/sự cố WMS–TMS end-to-end.
5. Báo cáo theo yêu cầu, số liệu kiểm chứng + PDF.
6. Recovery, chất lượng, quyền/egress và nghiệm thu MVP.

Giữ fixture DH001 làm luồng xuyên suốt; có ground truth logs/tickets/SOP và metrics, thêm near-collision IDs, duplicate, missing evidence, timezone boundary và provider failure. Roadmapper cần map requirements và điều chỉnh phase theo scope đã duyệt, không copy nguyên cấu trúc này.

## Confidence Assessment

| Nội dung | Mức tin cậy | Giới hạn |
|---|---|---|
| Khả năng SQL/vector/parser/API/PDF | High | Tài liệu chính thức, chưa kiểm tra compatibility toàn stack |
| Kiến trúc phù hợp MVP | Medium | Suy luận từ yêu cầu, chưa biết máy đích/quy mô |
| Embedding tiếng Việt/log và reranking | Medium/Low | Model card không thay benchmark dữ liệu logistics |
| Chỉ tiêu hiệu năng/chất lượng | Chưa xác định | Không bịa latency/accuracy hay hardware capacity |

## Gaps to Address

- Đã chốt Admin/Kỹ thuật viên; dataset ACL là baseline chưa được xác nhận riêng, có thể điều chỉnh khi discuss-phase 1.
- Đã chốt PDF text/DOCX/CSV/XLSX/TXT/JSON/JSONL/.log; không OCR/DOC/XLS cũ.
- Ticket import schema, timeline/priority mapping và quy tắc liên kết incident.
- Báo cáo theo yêu cầu đã chốt; timezone và quy tắc tính kỳ/duration phải công bố khi triển khai.
- Hardware, quy mô dữ liệu, LLM API provider và các chỉ tiêu nghiệm thu.
- Docker Compose/stack đã chốt; queue, parser cụ thể và package pins là lựa chọn triển khai cần kiểm chứng.

## Sources

Primary sources được liên kết chi tiết trong [STACK.md](STACK.md), [FEATURES.md](FEATURES.md), [ARCHITECTURE.md](ARCHITECTURE.md) và [PITFALLS.md](PITFALLS.md). Bối cảnh sản phẩm lấy từ [PROJECT.md](../PROJECT.md) và yêu cầu người dùng; không dùng thông tin sản phẩm cạnh tranh chưa kiểm chứng.

---
*Research completed: 2026-10-03. Ready for requirements scoping; initialization workflow remains in progress.*

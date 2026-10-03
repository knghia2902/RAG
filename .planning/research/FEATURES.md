# Feature Research

**Researched:** 2026-10-03
**Confidence:** HIGH về nhu cầu đã xác nhận; MEDIUM về các chức năng bổ sung được đề xuất.

## Feature Landscape

Các nhóm dưới đây dựa trên PROJECT.md và suy luận thiết kế cho bài toán này, không phải khảo sát thị trường hay cam kết scope mới.

| Nhóm cần có | Chức năng đề xuất | Độ phức tạp |
|---|---|---|
| Dữ liệu/tài liệu | Upload, danh sách, trạng thái xử lý, xem nguồn, xóa/reindex; xác thực format và lỗi parse | Medium |
| Chuẩn hóa | Log theo event/time/order/API; ticket theo ID/status/priority; bảng theo row/schema | High |
| Truy xuất | Mã định danh chính xác, tìm lexical/semantic, lọc nguồn/hệ thống/thời gian | High |
| Hỏi đáp | Câu trả lời có evidence, xem đoạn nguồn, nêu thiếu dữ liệu hoặc mâu thuẫn | Medium |
| Sự cố/ticket | Nhập ticket, tìm log/SOP/incident tương tự, timeline, giả thuyết và bước xử lý | High |
| Báo cáo | Chọn kỳ, số liệu xác định từ DB, nhận xét có nguồn, xem trước và PDF | High |
| Độ tin cậy | Bộ dữ liệu mẫu có ground truth, đánh giá retrieval/citation/report, lỗi provider rõ ràng | Medium |

## Differentiators

- Timeline WMS → API → TMS cho một đơn hàng; phân biệt lỗi đồng bộ và chậm cập nhật.
- Tách sự kiện đã quan sát, giả thuyết nguyên nhân và hướng kiểm chứng.
- Gom lỗi lặp theo quy tắc có thể kiểm tra; gợi ý SOP liên quan.
- Ghi phản hồi kỹ thuật viên để đánh giá chất lượng sau này.

Timeline/phân loại là đề xuất phù hợp nhu cầu; feedback UI, reranker và đánh giá nâng cao cần chốt scope riêng.

## Anti-Features

| Tránh trong MVP | Phương án phù hợp |
|---|---|
| Tự thao tác hệ thống thật | Đề xuất các bước để kỹ thuật viên duyệt/thực hiện |
| Nhận mọi định dạng không có giới hạn | Công bố support matrix; bắt đầu PDF text/DOCX/CSV/XLSX/TXT/JSONL nếu được chọn |
| Gọi mọi tương đồng là nguyên nhân | Nêu giả thuyết, bằng chứng và bước xác minh |
| Tính KPI bằng context top-k | Aggregate trên tập bản ghi đầy đủ theo bộ lọc |
| GraphRAG/multimodal ngay từ đầu | Baseline exact + lexical + dense, nâng cấp theo đo lường |

## Feature Dependencies

Upload → validation/parser → canonical data + provenance → indexing → retrieval → answers/analysis.

Structured import → chuẩn ID/time/status → dedup và liên kết ticket–incident → aggregate → report snapshot → narrative → PDF.

Source/version metadata cần có trước chunking. LLM provider abstraction cần có trước sinh câu trả lời. Xác thực và access filters, nếu đưa vào MVP, phải áp dụng cả structured queries lẫn vector retrieval và tải nguồn.

## MVP and Later

**Đã được người dùng yêu cầu:** Web, upload/quản lý dữ liệu, log/incident analysis, nhập/upload ticket, hỏi đáp, citations, báo cáo PDF, local storage, API backend, provider độc lập.

**Baseline yêu cầu:** job retry, xóa index, evidence thiếu/mâu thuẫn, time filters, source version, report counting rules và eval cố định. Người dùng đã chốt hai role Admin/Kỹ thuật viên; dataset là đơn vị quyền baseline đề xuất.

**Để sau:** Agent/tools, MCP adapter, connectors thật, Excel/Word export, OCR và scheduler báo cáo. SSO/RBAC chi tiết, feedback UI và reranking chưa đưa vào v1. PDF text/DOCX/CSV/XLSX/TXT/JSON/JSONL/.log và báo cáo kỳ/custom theo yêu cầu đã chốt.

## Prioritization

P1: ingestion/provenance, exact/hybrid retrieval, grounded answers, ticket analysis, deterministic report + PDF, baseline eval.

P2: OCR, feedback, reranker, lập lịch báo cáo, nâng cao dashboard.

P3: Agent/automation và connectors thật sau RAG ổn định.

## Sources

- [PROJECT.md](../PROJECT.md): phạm vi và luồng sử dụng đã được người dùng xác nhận.
- [Qdrant filtering](https://qdrant.tech/documentation/search/filtering/): khả năng lọc metadata.
- [Docling formats](https://docling-project.github.io/docling/usage/supported_formats/): cơ sở xây support matrix.
- [PostgreSQL aggregates](https://www.postgresql.org/docs/current/functions-aggregate.html): nền tảng tính số liệu; việc dùng cho báo cáo là đề xuất thiết kế của dự án.

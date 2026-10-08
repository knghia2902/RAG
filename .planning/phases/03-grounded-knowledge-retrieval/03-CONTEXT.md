# Phase 3: Grounded Knowledge Retrieval - Context

**Gathered:** 2026-10-08  
**Status:** Ready for planning

<domain>
## Phase Boundary

Người dùng (Admin hoặc Kỹ thuật viên) thực hiện hỏi đáp bằng tiếng Việt trên kho tri thức đã được nạp ở Phase 2, trong phạm vi các dataset được cấp quyền. Câu trả lời của hệ thống phải dựa trên bằng chứng truy xuất (grounded knowledge) thông qua LangChain RAG, PostgreSQL + pgvector và hai OpenAI provider adapters độc lập (Embedding Provider và LLM Generation Provider). Mọi câu khẳng định phải có trích dẫn nguồn có thể kiểm chứng với tọa độ provenance chính xác.

Yêu cầu thuộc phạm vi Phase 3: **RAG-01, RAG-02, RAG-03, RAG-04, RAG-05, SYS-02, SYS-03, SYS-05**.

Phase này tập trung vào pipeline RAG tri thức và giao diện Hỏi - Đáp có trích dẫn. Chưa triển khai phân tích chuyên sâu sự cố logistics WMS–TMS (Phase 4), chưa tạo báo cáo sự cố on-demand kèm xuất file PDF (Phase 5). Không sử dụng AI Agent tự hành, không gọi MCP và không thao tác trên hệ thống logistics thật.
</domain>

<decisions>
## Implementation Decisions

### Giao diện Hỏi - Đáp và Xem đoạn trích dẫn (Q&A UI & Evidence Preview)

- **D-01 (Bố cục 2 cột):** Giao diện Hỏi - Đáp thiết kế theo bố cục 2 cột:
  - Cột bên trái: Luồng hội thoại hỏi đáp chính, bao gồm hộp nhập câu hỏi, danh sách tin nhắn của người dùng và câu trả lời của AI. Các khẳng định có trích dẫn được đánh số dạng thẻ citation `[1]`, `[2]`.
  - Cột bên phải: Panel chi tiết trích dẫn nguồn (Evidence Preview Panel). Khi người dùng bấm vào một thẻ citation, panel lập tức mở ra hiển thị: đoạn văn bản trích dẫn gốc, tên tệp nguồn (`logical_filename`), phiên bản (`v{n}`), tên dataset và tọa độ chính xác (Trang đối với PDF, Dòng đối với Log/TXT, Sheet & Hàng đối với Excel/CSV, JSON Path đối với JSON/JSONL).
- **D-02 (Lưu trữ phiên & Lịch sử hội thoại):** Lưu trữ các phiên hỏi đáp (Chat sessions / threads) theo từng tài khoản vào cơ sở dữ liệu (`chat_sessions`, `chat_messages`):
  - Người dùng có danh sách lịch sử các phiên trò chuyện ở thanh bên để mở lại các cuộc hội thoại cũ.
  - Có nút "Cuộc trò chuyện mới" để khởi tạo phiên hỏi đáp mới.
  - Ngữ cảnh trò chuyện đa lượt (multi-turn context) được duy trì trong cùng một phiên, nhưng mỗi lượt truy xuất RAG vẫn chỉ nạp các đoạn bằng chứng liên quan trong giới hạn token budget.
- **D-03 (Bộ lọc phạm vi truy xuất tùy chọn):**
  - Mặc định: Hệ thống tìm kiếm và truy xuất trên toàn bộ các dataset mà tài khoản người dùng đang được cấp quyền.
  - Bộ lọc nâng cao: Cung cấp thanh công cụ bộ lọc có thể mở rộng (Scope Filters: chọn Dataset cụ thể, chọn loại tài liệu SOP/Log/Ticket/Bảng vận hành, chọn khoảng thời gian) ở đầu khung chat để người dùng chủ động thu hẹp phạm vi khi cần tra cứu tập trung.
- **D-04 (Cảnh báo trực quan khi thiếu thông tin hoặc mâu thuẫn):**
  - Khi bằng chứng truy xuất không đủ để trả lời chắc chắn hoặc phát hiện mâu thuẫn giữa các nguồn tài liệu (RAG-05):
    - Câu trả lời tự nhiên của AI nêu rõ các điểm chưa biết, các giả thuyết chưa được xác nhận và nguyên nhân mâu thuẫn.
    - Giao diện hiển thị thêm Banner/Huy hiệu cảnh báo trực quan màu vàng ("Thiếu dữ liệu xác thực" hoặc "Phát hiện mâu thuẫn giữa các nguồn") ngay trên khối tin nhắn để kỹ thuật viên nhận diện tức thì.
- **D-05 (Kiểm tra quyền thời gian thực - Live Scope Recheck):**
  - Mang sang từ Phase 1 và Phase 2 (`recheck_response`): Khi người dùng bấm vào citation để xem chi tiết đoạn trích ở Panel bên phải hoặc khi tải lại lịch sử tin nhắn cũ, backend lập tức tái kiểm tra quyền dataset hiện tại của tài khoản.
  - Nếu quyền trên dataset của nguồn đó đã bị Admin thu hồi, nội dung đoạn trích sẽ bị chặn kèm thông báo rõ ràng "Quyền truy cập nguồn dữ liệu đã thay đổi hoặc bị thu hồi", không để lộ thông tin nguồn.
- **D-06 (Che giấu Secret & Token Budget Egress):**
  - Áp dụng bộ lọc che secret (Sample token/key masking) ở cả hai đường: trước khi gửi embedding chunk/query và trước khi gửi generation context sang OpenAI API (SYS-03).
  - Áp dụng token budget nghiêm ngặt cho generation context, không gửi toàn bộ tài liệu nguyên bản.

### the agent's Discretion

- Thiết kế cấu trúc bảng cơ sở dữ liệu cho lịch sử chat (`chat_sessions`, `chat_messages`, `chat_citations`) liên kết an toàn với `Account` và `CanonicalRecord`.
- Chọn chiến lược chunking và vector store adapter (`LangChain pgvector`) tương thích phiên bản pgvector 0.8.7 và PostgreSQL 18 hiện có.
- Cơ chế Hybrid Retrieval: Kết hợp tìm kiếm chính xác (Exact Identifier Matching trên mã đơn hàng `DH001`, `ERR-502`) với tìm kiếm ngữ nghĩa dense embedding (pgvector) để đảm bảo không bị nhầm lẫn giữa các mã tương tự như `DH001` và `DH010` (RAG-02).
- Thiết kế Provider Interfaces độc lập: `EmbeddingProvider` và `LLMProvider` với Fake/Mock adapters cho test suite và OpenAI adapters cho chạy thực tế.
- Giao diện Admin cấu hình model tại trang `/configuration`: hiển thị trạng thái model, dimension, index version và cho phép thiết lập API key/model name.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Scope and Architecture
- `.planning/PROJECT.md` — Mục tiêu dự án, stack công nghệ, nguyên tắc trích dẫn và giới hạn bảo mật.
- `.planning/REQUIREMENTS.md` § RAG and Evidence — Yêu cầu chi tiết RAG-01 đến RAG-05, SYS-02, SYS-03, SYS-05.
- `.planning/ROADMAP.md` § Phase 3 — Mục tiêu giai đoạn và các tiêu chí thành công (Success Criteria).
- `docs/security-contracts.md` — Yêu cầu bảo mật API, che giấu đường dẫn tệp và kiểm tra quyền thời gian thực.

### Prior Context and Contracts
- `.planning/phases/01-local-workspace-and-access-control/01-CONTEXT.md` — Quyết định về tài khoản, vai trò Admin/Kỹ thuật viên, dataset ACL.
- `.planning/phases/02-dataset-ingestion-and-source-lifecycle/02-CONTEXT.md` — Quyết định về vòng đời nguồn, phiên bản active, 5 published profiles và tọa độ `SourceLocator`.
- `backend/app/rag/contracts.py` — Hợp đồng DTO: `SourceLocator`, `EvidenceChunk`, `AuthorizedScope`, `RetrievalRequest`, `EmbeddingIndex`.
- `backend/app/llm/contracts.py` — Hợp đồng DTO: `GenerationRequest`, `GenerationResult`, `LLMProvider`.
- `backend/app/auth/policy.py` — Cơ chế phân quyền dataset và kiểm tra capability.
- `backend/app/database/models/source.py` — Cấu trúc dữ liệu `Source`, `SourceVersion`, `CanonicalRecord`.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `backend/app/rag/contracts.py`: Đã có sẵn định nghĩa `SourceLocator` (đầy đủ tọa độ page, section, sheet, row, line_start, line_end, json_path), `EvidenceChunk`, `EmbeddingIndex` và các Protocol interface.
- `backend/app/llm/contracts.py`: Đã có sẵn `GenerationRequest`, `GenerationResult` và `LLMProvider` protocol.
- `backend/app/database/models/source.py`: Đã có bảng `canonical_records` chứa dữ liệu văn bản sạch đã chuẩn hóa theo 5 profile kèm locator chi tiết.
- `backend/app/auth/policy.py`: Hàm `recheck_response()` và `require_dataset_access()` sẵn sàng tích hợp vào các endpoint hỏi đáp.
- `frontend/src/app/(workspace)/layout.tsx`: Layout thanh điều hướng sẵn sàng bổ sung liên kết đến trang Hỏi - Đáp.

### Established Patterns
- FastAPI dependency injection (`get_current_user`, `require_authenticated`).
- DTOs bất biến sử dụng Pydantic V2 (`extra="forbid"`, `frozen=True`).
- Giao diện tiếng Việt nhất quán, tuân thủ tiêu chuẩn trợ năng ARIA cho modal/dialog/panel.

### Integration Points
- `backend/app/rag/`: Triển khai embedding generator, pgvector indexing và hybrid retriever.
- `backend/app/llm/`: Triển khai OpenAI LLM generation adapter và secret masking filter.
- `backend/app/api/`: Thêm router `/api/v1/chat` (quản lý session, gửi tin nhắn, streaming/trả lời, preview trích dẫn).
- `frontend/src/app/(workspace)/chat/`: Màn hình giao diện Hỏi - Đáp 2 cột (hoặc trang `/qa`).

</code_context>

<specifics>
## Specific Ideas

- Mã đơn hàng ví dụ `DH001` vs `DH010`: Tra cứu phải phân biệt chính xác tuyệt đối qua exact lexical match trước khi kết hợp vector distance.
- Thẻ citation trên UI: Hiển thị nhỏ gọn dạng `[1]`, `[2]` với tooltip hiển thị nhanh tên file, khi click sẽ mở panel chi tiết bên phải.
- Panel trích dẫn bên phải: Có nút đóng panel, hiển thị rõ badge loại tọa độ (ví dụ: `Trang 3`, `Dòng 12-18`, `Sheet: Inventory, Hàng: 45`, `JSON: /items/2`).

</specifics>

<deferred>
## Deferred Ideas

- Chức năng xuất toàn bộ phiên hội thoại ra PDF: Thuộc Phase 5 (On-Demand Incident Reports and PDF).
- Chức năng tự động liên kết hội thoại với Ticket / Incident cụ thể: Thuộc Phase 4 (Logistics Incident and Ticket Analysis).
- AI Agent gọi công cụ bên ngoài hoặc MCP: Dành cho giai đoạn mở rộng sau MVP.

</deferred>

---

*Phase: 03-grounded-knowledge-retrieval*  
*Context gathered: 2026-10-08*

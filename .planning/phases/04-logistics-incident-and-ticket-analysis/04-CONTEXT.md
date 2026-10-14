# Phase 4: Logistics Incident and Ticket Analysis - Context

**Gathered:** 2026-10-14  
**Status:** Ready for planning

<domain>
## Phase Boundary

Kỹ thuật viên IT và logistics phân tích các sự cố đồng bộ WMS–TMS thông qua mô tả, mã đơn hàng (order ID, ví dụ `DH001`), hoặc tải lên tệp ticket theo schema công bố (JSON/CSV). Hệ thống thực hiện truy xuất bằng chứng từ log đa hệ thống, liên kết chuỗi sự kiện theo correlation ID và timestamp, phân loại nhóm lỗi, xác định hệ thống bị ảnh hưởng, đánh giá mức độ ưu tiên đề xuất, đưa ra các giả thuyết nguyên nhân gốc rễ và đề xuất các bước kiểm tra/khắc phục có trích dẫn từ quy trình chuẩn SOP và tiền lệ sự cố tương tự.

Yêu cầu thuộc phạm vi Phase 4: **INC-01, INC-02, INC-03, INC-04, INC-05, EVAL-01**.

Ranh giới bảo mật & thẩm quyền MVP:
- Toàn bộ phân tích dựa trên dữ liệu mẫu đã nạp trong phạm vi dataset được cấp quyền của tài khoản.
- Áp dụng Live Scope Recheck: Khi quyền dataset bị thu hồi, mọi yêu cầu phân tích mới hoặc xem lại chi tiết trích dẫn lập tức bị chặn với mã 403.
- Hệ thống chỉ thực hiện phân tích và đề xuất có nguồn trích dẫn kiểm chứng được; tuyệt đối không gọi AI Agent tự hành, không gọi tools, không gửi thông báo ra bên ngoài, không cập nhật ticket thật và không thực hiện thao tác trên hệ thống WMS/TMS thật.
</domain>

<decisions>
## Implementation Decisions

### Giao diện & Phương thức tiếp nhận sự cố (Incident Input & Ticket Intake)

- **D-01 (Trang chuyên biệt & Phương thức nhập linh hoạt):** Cung cấp trang chuyên biệt `/incidents` trên thanh Sidebar (dành cho cả Kỹ thuật viên và Quản trị viên). Trang hỗ trợ 2 chế độ nhập dữ liệu đầu vào:
  1. *Chế độ nhập nhanh (Quick Form):* Nhập Mã đơn hàng (Order ID, ví dụ `DH001`), mô tả tóm tắt sự cố, kèm các bộ lọc tùy chọn theo hệ thống (WMS, TMS, API Gateway, hoặc Tất cả) và khoảng thời gian phát sinh.
  2. *Chế độ tải tệp Ticket (Upload Ticket File):* Cho phép tải lên tệp ticket theo định dạng JSON hoặc CSV tuân thủ schema công bố (`ticket_id`, `order_id`, `timestamp`, `system`, `severity`, `description`).
- **D-02 (Kiểm tra Schema nghiêm ngặt khi Upload):**
  - Khi người dùng tải lên tệp ticket (JSON/CSV), hệ thống kiểm tra tính hợp lệ của schema ngay lập tức.
  - Nếu tệp vi phạm cấu trúc hoặc thiếu các trường bắt buộc, hệ thống từ chối phân tích và hiển thị thông báo lỗi chi tiết đến từng số dòng và tên trường vi phạm (ví dụ: *"Dòng 3: Thiếu trường bắt buộc 'order_id'"*), ngăn ngừa dữ liệu hỏng làm sai lệch kết quả phân tích.

### Trình bày kết quả & Dòng thời gian sự kiện (Analysis Output & Event Timeline)

- **D-03 (Bố cục Dashboard chuyên sâu 4 khối):** Kết quả phân tích sự cố được trình bày trực quan và mạch lạc qua 4 khối chức năng:
  1. *Khối 1: Tóm tắt sự cố & Phân loại tự động:* Hiển thị rõ Nhóm lỗi (Lệch trạng thái, Timeout kết nối, Thiếu kiện hàng...), Hệ thống liên quan chính (WMS / TMS / API Gateway) và Mức độ ưu tiên đề xuất (P1 - Nghiêm trọng đến P4 - Thấp).
  2. *Khối 2: Trục dòng thời gian sự kiện đa hệ thống (Multi-system Event Timeline):* Liệt kê chuỗi log theo trình tự thời gian WMS -> API Gateway -> TMS liên quan đến mã đơn hàng, giúp kỹ thuật viên nắm bắt luồng dữ liệu end-to-end.
  3. *Khối 3: Giả thuyết nguyên nhân & Dữ liệu còn thiếu:* Phân biệt rành mạch giữa các *Giả thuyết nguyên nhân gốc rễ* (Root cause hypotheses) với *Nguyên nhân đã xác nhận*, đồng thời liệt kê rõ các khoảng trống thông tin/dữ liệu còn thiếu chưa đủ bằng chứng kết luận (tuân thủ RAG-05).
  4. *Khối 4: Khuyến nghị & Quy trình xử lý đề xuất:* Đưa ra các bước kiểm tra và xử lý cụ thể, có đối chiếu và trích dẫn trực tiếp từ quy trình SOP chuẩn tương ứng (ví dụ: `SOP-LOG-01`).
- **D-04 (Trục thời gian phân màu theo hệ thống & Điểm gãy đồng bộ):**
  - Mỗi sự kiện trên Trục dòng thời gian được gắn nhãn màu đặc trưng theo hệ thống (ví dụ: Xanh lam cho WMS, Tím cho API Gateway, Cam cho TMS).
  - Điểm phát sinh lỗi hoặc đứt gãy đồng bộ đầu tiên (sync failure point) được làm nổi bật với viền đỏ và biểu tượng cảnh báo lỗi để kỹ thuật viên nhận diện tức thì.
  - Mỗi node sự kiện cho phép nhấp vào để mở xem ngay đoạn log trích dẫn gốc kèm tọa độ provenance (file, dòng log).

### the agent's Discretion

- Thiết kế module nghiệp vụ `backend/app/modules/log_analysis` và `backend/app/modules/tickets` tách biệt, gọi qua Service layer sạch.
- Thiết kế các DTOs Pydantic v2 cho Ticket import schema, Incident Analysis Request/Response contracts.
- Lưu trữ lịch sử phân tích sự cố (`incident_analyses`) trong database liên kết với tài khoản thực hiện để tra cứu lại và phục vụ trích xuất số liệu báo cáo ở Phase 5.
- Thiết kế cơ chế đối soát liên chuỗi log (Cross-system Log Correlation) dựa trên `order_id` hoặc correlation trace id, sắp xếp theo timestamp tăng dần và không lẫn lộn giữa các mã tương tự như `DH001` và `DH010`.
- Tạo bộ fixture dữ liệu mẫu logistics hoàn chỉnh (`data/sample/logistics_incidents/`) bao gồm log WMS, log TMS, log API Gateway, danh sách ticket mẫu và SOP mẫu để phục vụ kiểm chứng `EVAL-01`.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Requirements and Architecture
- `.planning/PROJECT.md` — Mục tiêu phân tích sự cố IT & Logistics, nguyên tắc trích dẫn nguồn và giới hạn MVP.
- `.planning/REQUIREMENTS.md` § Incident and Ticket Analysis — Yêu cầu chi tiết INC-01, INC-02, INC-03, INC-04, INC-05, EVAL-01.
- `.planning/ROADMAP.md` § Phase 4 — Tiêu chí thành công của Phase 4.
- `docs/security-contracts.md` — Quy định bảo mật, che giấu đường dẫn và kiểm tra quyền thời gian thực.

### Prior Context and Interfaces
- `.planning/phases/01-local-workspace-and-access-control/01-CONTEXT.md` — Tài khoản, vai trò và phân quyền dataset.
- `.planning/phases/02-dataset-ingestion-and-source-lifecycle/02-CONTEXT.md` — Định dạng dữ liệu và tọa độ `SourceLocator`.
- `.planning/phases/03-grounded-knowledge-retrieval/03-CONTEXT.md` — Cơ chế Hybrid Retrieval, Provider Adapters và thẻ trích dẫn `[1]`.
- `backend/app/rag/contracts.py` — Hợp đồng DTO: `SourceLocator`, `EvidenceChunk`, `AuthorizedScope`.
- `backend/app/llm/contracts.py` — Hợp đồng DTO: `GenerationRequest`, `GenerationResult`, `LLMProvider`.
- `backend/app/auth/policy.py` — Cơ chế phân quyền dataset và kiểm tra quyền truy cập.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `backend/app/modules/log_analysis/` và `backend/app/modules/tickets/`: Các module rỗng đã được định vị trong kiến trúc backend sẵn sàng cài đặt logic nghiệp vụ.
- `backend/app/rag/retriever.py` & `backend/app/rag/pgvector_store.py`: Cơ chế tìm kiếm kết hợp (lexical exact match + vector search) đã hoàn thiện ở Phase 3 để truy xuất chính xác log và SOP.
- `backend/app/llm/openai_provider.py` & `backend/app/llm/masking.py`: Provider LLM và bộ lọc che secret sẵn sàng phục vụ sinh phân tích sự cố.
- `frontend/src/components/Sidebar.tsx`: Thanh điều hướng sẵn sàng bổ sung mục "Phân tích sự cố" dẫn tới `/incidents`.

### Established Patterns
- Pydantic v2 strict models (`extra="forbid"`, `frozen=True`).
- FastAPI dependency injection cho xác thực và phân quyền (`get_current_user`, `require_authenticated`).
- UI component chuẩn giao diện tiếng Việt, hỗ trợ trạng thái tải và thông báo lỗi rõ ràng.

### Integration Points
- Backend: Tạo router `/api/v1/incidents` cung cấp các endpoint phân tích sự cố, tải tệp ticket, xem lịch sử và tra cứu chi tiết dòng log.
- Frontend: Tạo trang `frontend/src/app/(workspace)/incidents/page.tsx` và các component Dashboard 4 khối, Event Timeline trực quan.

</code_context>

<specifics>
## Specific Ideas

- Kịch bản đối soát sự cố `DH001`:
  - WMS log ghi nhận đóng gói thành công lúc 08:15:00.
  - API Gateway ghi nhận request chuyển tiếp sang TMS lúc 08:15:05 nhưng timeout (504 Gateway Timeout).
  - TMS log không ghi nhận mã vận đơn tương ứng hoặc ghi nhận trạng thái pending sync.
  - Phân tích chỉ ra rõ điểm gãy tại API Gateway và đề xuất kiểm tra kết nối mạng/retry sync theo SOP-LOG-01.
  - Phân biệt rõ ràng với đơn hàng `DH010` (vốn là đơn giao thành công, không có lỗi timeout).
- Huy hiệu trực quan:
  - Hệ thống: WMS (Badge Xanh lam), API Gateway (Badge Tím), TMS (Badge Cam).
  - Mức độ ưu tiên: P1 (Đỏ), P2 (Cam), P3 (Vàng), P4 (Xanh lục).
  - Nguồn bằng chứng: Log sự cố (Badge Xám), Tiền lệ tương tự (Badge Xanh dương), Quy trình chuẩn SOP (Badge Xanh lá).

</specifics>

<deferred>
## Deferred Ideas

- Chức năng tự động bắn webhook hoặc cập nhật trạng thái vào hệ thống WMS/TMS thật: Dành cho phiên bản mở rộng có AI Agent (EXT-04).
- Kết nối trực tiếp vào cơ sở dữ liệu live của WMS/TMS (live database connectors): Dành cho v2 (EXT-06).
- Xuất toàn bộ báo cáo phân tích sự cố ra file PDF: Thuộc Phase 5 (On-Demand Incident Reports and PDF).

</deferred>

---

*Phase: 04-logistics-incident-and-ticket-analysis*  
*Context gathered: 2026-10-14*

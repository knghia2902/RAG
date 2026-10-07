# Requirements: Modular RAG cho IT & Logistics

**Defined:** 2026-10-03
**Status:** v1 scope defined from user decisions; Phase 1 requirements are validated or explicitly carried forward at the Phase 1 policy-contract boundary. Remaining v1 requirements are still active in later phases.
**Core Value:** Kỹ thuật viên tìm bằng chứng và nhận phân tích, đề xuất xử lý sự cố logistics kèm nguồn để kiểm tra.

## v1 Requirements

### Authentication and Authorization

- [ ] **AUTH-01**: Admin và Kỹ thuật viên có thể đăng nhập bằng tài khoản/mật khẩu và đăng xuất; tài khoản bị vô hiệu hóa không còn truy cập được API.
- [ ] **AUTH-02**: Admin có thể tạo tài khoản, gán role, vô hiệu hóa tài khoản và đặt lại mật khẩu.
- [ ] **AUTH-03**: Admin có thể cấp/thu hồi quyền truy cập dataset cho Kỹ thuật viên; dataset là đơn vị cấp phạm vi MVP được đề xuất.
- [ ] **AUTH-04**: Kỹ thuật viên chỉ có thể tìm kiếm, phân tích, xem/tải nguồn và tạo/xem báo cáo trong phạm vi được cấp quyền; backend kiểm tra quyền trên mọi đường dữ liệu, kể cả lịch sử kết quả và PDF.
- [ ] **AUTH-05**: Admin có thể xem toàn bộ báo cáo; mô hình role/permission cho phép thêm role mà không sửa RAG Core.

### Data and Document Management

- [x] **DATA-01**: Admin có thể tạo dataset, upload tài liệu/dữ liệu vào dataset và xem danh sách cùng metadata nguồn.
- [x] **DATA-02**: Admin có thể nhập PDF có text, DOCX, CSV, XLSX, TXT, JSON, JSONL và .log; dữ liệu không hợp lệ/không hỗ trợ được báo lỗi rõ ràng, không âm thầm đánh dấu thành công.
- [x] **DATA-03**: Admin có thể xem trạng thái xử lý và lỗi ingestion, thử lại job lỗi; retry không nhân đôi bản ghi và trạng thái có thể khôi phục sau restart.
- [x] **DATA-04**: Người dùng được cấp quyền có thể xem đoạn nguồn với version và locator: trang/section, sheet/row, JSON record/path hoặc dòng/event log tương ứng.
- [x] **DATA-05**: Admin có thể xóa nguồn và lập chỉ mục lại; nguồn đã xóa hoặc version không còn active không được dùng trong lần truy xuất mới.
- [x] **DATA-06**: Dữ liệu log/ticket/incident/bảng được chuẩn hóa theo schema công bố trước import, giữ ID, hệ thống, trạng thái/ưu tiên, timestamp và nguồn; bản ghi thiếu trường/lỗi được phản ánh trong kết quả import.

### RAG and Evidence

- [ ] **RAG-01**: Người dùng có thể hỏi đáp bằng tiếng Việt về dữ liệu được phép truy cập và nhận câu trả lời dựa trên bằng chứng truy xuất.
- [ ] **RAG-02**: Người dùng có thể tra cứu theo order ID, error code hoặc correlation ID chính xác và kết hợp truy xuất lexical/ngữ nghĩa cho tài liệu liên quan; fixture DH001 không bị lẫn DH010.
- [ ] **RAG-03**: Người dùng có thể giới hạn truy xuất theo dataset, loại nguồn, hệ thống và khoảng thời gian khi nguồn có metadata tương ứng.
- [ ] **RAG-04**: Người dùng có thể mở nguồn/đoạn dữ liệu được trích dẫn cho nhận định trong kết quả; server không chấp nhận citation ID ngoài tập evidence của lần truy xuất.
- [ ] **RAG-05**: Khi bằng chứng thiếu hoặc mâu thuẫn, người dùng nhận thông báo rõ phần chưa biết/mâu thuẫn; hệ thống không trình bày giả thuyết như nguyên nhân đã xác nhận.

### Incident and Ticket Analysis

- [ ] **INC-01**: Kỹ thuật viên có thể phân tích sự cố bằng mô tả, mã đơn hàng và bộ lọc; kết quả tổng hợp log liên quan, hệ thống và trình tự sự kiện có nguồn.
- [ ] **INC-02**: Kỹ thuật viên có thể nhập ticket hoặc upload ticket theo schema import được công bố để yêu cầu phân tích.
- [ ] **INC-03**: Kỹ thuật viên nhận phân loại nhóm lỗi, hệ thống liên quan và ưu tiên đề xuất từ ticket/bằng chứng; thông tin nguồn và đề xuất được phân biệt.
- [ ] **INC-04**: Kỹ thuật viên xem SOP, ticket và incident tương tự liên quan đến vấn đề; precedent cũ được phân biệt với bằng chứng sự cố hiện tại.
- [ ] **INC-05**: Kỹ thuật viên nhận các giả thuyết nguyên nhân, bằng chứng, thông tin còn thiếu và bước kiểm tra/xử lý đề xuất; MVP không gọi tools hay thao tác hệ thống thật.

### On-Demand Reporting

- [ ] **REP-01**: Người dùng có thể tạo báo cáo theo ngày, tuần, tháng hoặc khoảng thời gian tùy chọn trong phạm vi dataset được phép, với timezone và biên kỳ hiển thị rõ.
- [ ] **REP-02**: Người dùng nhận tổng số ticket và số incident riêng, nhóm lỗi, mức ưu tiên, hệ thống liên quan và trạng thái xử lý; số liệu tính trên toàn bộ bản ghi trong scope bằng quy tắc xác định, không từ context top-k.
- [ ] **REP-03**: Người dùng xem thời gian phát sinh, xử lý và nguyên nhân đã xác định nếu có; bản ghi chưa xử lý/thiếu timestamp/thiếu nguyên nhân được hiển thị là chưa biết thay vì suy đoán.
- [ ] **REP-04**: Người dùng xem lỗi lặp lại theo quy tắc grouping công bố và nhận đề xuất/hướng xử lý kèm bằng chứng.
- [ ] **REP-05**: Người dùng xem nguồn dữ liệu, bộ lọc, kỳ và snapshot/version được dùng để tạo báo cáo và có thể mở bằng chứng trong phạm vi quyền hiện tại.
- [ ] **REP-06**: Người dùng có thể xem trước, tải PDF có tiếng Việt và mở lại báo cáo đã tạo; truy cập lại bị từ chối nếu quyền đối với dữ liệu liên quan đã bị thu hồi.

### Administration and Architecture

- [ ] **SYS-01**: Người vận hành có thể chạy FastAPI, Next.js/TypeScript, PostgreSQL + pgvector và file storage local bằng Docker Compose; MVP sử dụng OpenAI Embeddings và OpenAI API generation bên ngoài.
- [ ] **SYS-02**: Admin có thể cấu hình LLM và embedding provider/model trên backend; hai provider tách riêng để thay Gemini/local generation hoặc local embedding về sau, secrets không lộ trong Web/kết quả và index lưu model/dimension/version.
- [ ] **SYS-03**: Generation chỉ gửi context truy xuất liên quan trong phạm vi quyền và token budget; embedding gửi các chunk cần index và query qua OpenAI API; rules che secret được kiểm chứng bằng token/key mẫu trước egress ở cả hai đường.
- [ ] **SYS-04**: Next.js Web dùng FastAPI contracts; pipeline LangChain, parser, Embedding Provider, LLM Provider và các module log_analysis/tickets/reports có boundary rõ theo cấu trúc backend/app đã chốt, cho phép thêm OCR/MCP/scheduler/Agent sau này.
- [ ] **SYS-05**: Khi ingestion hoặc LLM lỗi/timeout, người dùng nhận trạng thái và lý do rõ; hệ thống không hiển thị nội dung giả như kết quả thành công.

### Evaluation and Acceptance

- [ ] **EVAL-01**: Nhóm dự án có thể chạy bộ dữ liệu mẫu WMS/TMS/API, SOP, ticket, incident và bảng logistics, gồm DH001 và đáp án/metrics chuẩn để kiểm chứng luồng Web end-to-end.
- [ ] **EVAL-02**: Nhóm dự án có thể chạy đánh giá tái lập cho ID gần giống, thiếu/mâu thuẫn evidence, citation support, prompt injection, dữ liệu ngoài quyền, duplicate import, thu hồi quyền và nguồn đã xóa.
- [ ] **EVAL-03**: Nhóm dự án có thể đối chiếu metrics/PDF với ground truth, gồm biên kỳ/timezone, incident đang mở và ticket–incident liên quan; đo thời gian ingestion/truy xuất/generation trên máy đích và ghi giới hạn quan sát được.

## v2 Requirements

- **EXT-01**: OCR cho PDF scan/hình ảnh qua parser adapter.
- **EXT-02**: Scheduler tạo/gửi báo cáo định kỳ qua Report Service.
- **EXT-03**: MCP adapter dùng service/API và quyền truy cập hiện có.
- **EXT-04**: Agent/tools kiểm tra API, chạy lại đồng bộ, cập nhật ticket hoặc gửi thông báo với phân quyền và phê duyệt.
- **EXT-05**: Export Excel/Word.
- **EXT-06**: Connectors thật WMS/TMS/ticket/monitoring.
- **EXT-07**: Adapter LLM chạy local hoàn chỉnh và kiểm chứng triển khai nội bộ hoàn toàn.
- **EXT-08**: Local Embedding Provider, reindex theo model/dimension mới và kiểm chứng truy xuất; Gemini LLM adapter.

## Out of Scope

| Capability | Reason |
|------------|--------|
| OCR, scheduler, MCP và Agent/tools trong v1 | Người dùng đã dành cho giai đoạn mở rộng |
| Thao tác hệ thống thật | MVP chỉ phân tích/đề xuất và dùng dữ liệu mẫu |
| DOC/XLS legacy và format ngoài danh sách v1 | Chưa được yêu cầu; DOCX/XLSX là scope ban đầu |
| SSO/LDAP, giao diện tùy biến role và phân quyền theo từng dòng | Chưa chốt; MVP đề xuất hai role và cấp quyền dataset |
| Tự động thực thi SQL do LLM sinh | Số liệu dùng query/report rules do ứng dụng kiểm soát |
| SLA enterprise hoặc accuracy/latency chưa đo | Chưa có quy mô/máy đích và benchmark |

## Acceptance Criteria

Mỗi yêu cầu v1 phải có evidence nghiệm thu phù hợp. Bộ eval phải kiểm tra cả retrieval và hỗ trợ claim, không chỉ citation tồn tại. Quyền phải được thử qua API trực tiếp, lịch sử và PDF. Các ca xác định về quyền, ID, số liệu và vòng đời nguồn phải khớp expected fixture; chỉ tiêu chất lượng/hiệu năng rộng hơn sẽ chốt khi lập kế hoạch từ baseline đo được.

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| AUTH-01 | Phase 1 | Validated |
| AUTH-02 | Phase 1 | Validated |
| AUTH-03 | Phase 1 | Validated |
| AUTH-04 | Phase 1 | Policy contract validated; source/retrieval/history/report/PDF checks carry forward |
| AUTH-05 | Phase 1 | Capability contract validated; report endpoint carries forward |
| DATA-01 | Phase 2 | Validated |
| DATA-02 | Phase 2 | Validated |
| DATA-03 | Phase 2 | Validated |
| DATA-04 | Phase 2 | Validated |
| DATA-05 | Phase 2 | Validated |
| DATA-06 | Phase 2 | Validated |
| RAG-01 | Phase 3 | Pending |
| RAG-02 | Phase 3 | Pending |
| RAG-03 | Phase 3 | Pending |
| RAG-04 | Phase 3 | Pending |
| RAG-05 | Phase 3 | Pending |
| INC-01 | Phase 4 | Pending |
| INC-02 | Phase 4 | Pending |
| INC-03 | Phase 4 | Pending |
| INC-04 | Phase 4 | Pending |
| INC-05 | Phase 4 | Pending |
| REP-01 | Phase 5 | Pending |
| REP-02 | Phase 5 | Pending |
| REP-03 | Phase 5 | Pending |
| REP-04 | Phase 5 | Pending |
| REP-05 | Phase 5 | Pending |
| REP-06 | Phase 5 | Pending |
| SYS-01 | Phase 1 | Validated |
| SYS-02 | Phase 3 | Pending |
| SYS-03 | Phase 3 | Pending |
| SYS-04 | Phase 1 | Validated |
| SYS-05 | Phase 3 | Pending |
| EVAL-01 | Phase 4 | Pending |
| EVAL-02 | Phase 6 | Pending |
| EVAL-03 | Phase 6 | Pending |

**Coverage:**
- v1 requirements: 35
- Mapped to phases: 35
- Unmapped: 0

---
*Last updated: 2026-10-03 after user locked the Modular RAG stack; traceability maintained with roadmap.*

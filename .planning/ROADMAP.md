# Roadmap: Modular RAG cho IT & Logistics

## Overview

MVP Web theo các luồng sử dụng end-to-end: quản trị/quyền → dữ liệu → hỏi đáp có nguồn → phân tích sự cố/ticket → báo cáo PDF → nghiệm thu. Stack đã chốt Python/FastAPI, LangChain, PostgreSQL/pgvector, OpenAI Embeddings và LLM API, Next.js/TypeScript, Docker Compose. Cấu trúc code theo PROJECT.md. Đây là roadmap khởi tạo, chưa triển khai ứng dụng.

Workflow tự động, granularity standard, kế hoạch độc lập có thể chạy song song khi không xung đột dependency/ownership. Vertical MVP là phương án tổ chức mặc định phù hợp mục tiêu MVP người dùng chốt. Dataset ACL là baseline thiết kế, cần cụ thể hóa ở phase 1. Không thực hiện Agent, MCP, OCR hoặc scheduler trong milestone này.

## Phases

- [ ] **Phase 1: Local Workspace and Access Control** - Chạy Web/API/database local và sử dụng tài khoản Admin/Kỹ thuật viên với quyền dataset.
- [ ] **Phase 2: Dataset Ingestion and Source Lifecycle** - Upload đa định dạng, chuẩn hóa dữ liệu và quản lý nguồn có provenance.
- [ ] **Phase 3: Grounded Knowledge Retrieval** - Hỏi đáp LangChain/pgvector qua OpenAI providers, truy xuất chính xác và xem bằng chứng.
- [ ] **Phase 4: Logistics Incident and Ticket Analysis** - Phân tích log/ticket WMS–TMS, giả thuyết nguyên nhân và đề xuất xử lý có nguồn.
- [ ] **Phase 5: On-Demand Incident Reports and PDF** - Báo cáo số liệu xác định theo kỳ/custom, nhận xét có nguồn và PDF.
- [ ] **Phase 6: MVP Reliability and Acceptance** - Kiểm chứng chất lượng, quyền, vòng đời dữ liệu, báo cáo và giới hạn hiệu năng.

## Phase Details

### Phase 1: Local Workspace and Access Control

**Goal:** Admin/Kỹ thuật viên sử dụng được Web local, đăng nhập và quản lý tài khoản/phạm vi dataset qua FastAPI với các boundary module đã chốt.
**Mode:** mvp
**Depends on:** Nothing (first phase)
**Requirements:** AUTH-01, AUTH-02, AUTH-03, AUTH-04, AUTH-05, SYS-01, SYS-04
**UI hint:** yes
**Success Criteria:**

1. Người vận hành khởi động Next.js, FastAPI và PostgreSQL/pgvector qua Docker Compose theo cấu hình mẫu không chứa secrets thật; dữ liệu giữ được qua restart.
2. Admin đăng nhập, tạo/gán role/đặt lại mật khẩu/vô hiệu hóa tài khoản; Kỹ thuật viên đăng nhập/đăng xuất và bị từ chối API sau vô hiệu hóa.
3. Admin tạo workspace dataset metadata và cấp/thu hồi quyền; Kỹ thuật viên không đọc metadata của dataset ngoài quyền qua UI hoặc API trực tiếp.
4. Mô hình role/permission và policy dataset có contract dùng chung cho các module; các endpoint dữ liệu/lịch sử/nguồn/PDF bổ sung ở phase sau phải dùng policy này và có acceptance check ngay khi triển khai.
5. Cấu trúc backend/app/{api,rag,llm,modules,database,auth}, frontend và data/storage được tạo đúng; Web dùng API contract, module/provider contracts cho phép thay adapter mà không sửa nghiệp vụ.

**Plans:** 1/5 plans executed across 5 waves (ready to execute)
**Wave 1**

- [x] 01-01-PLAN.md

**Wave 2** *(blocked on Wave 1 completion)*

- [ ] 01-02-PLAN.md

**Wave 3** *(blocked on Wave 2 completion)*

- [ ] 01-03-PLAN.md

**Wave 4** *(blocked on Wave 3 completion)*

- [ ] 01-04-PLAN.md

**Wave 5** *(blocked on Wave 4 completion)*

- [ ] 01-05-PLAN.md

### Phase 2: Dataset Ingestion and Source Lifecycle

**Goal:** Admin nhập và quản lý dữ liệu đa định dạng trên Web; người được cấp quyền kiểm tra được nội dung nguồn và kết quả xử lý.
**Mode:** mvp
**Depends on:** Phase 1
**Requirements:** DATA-01, DATA-02, DATA-03, DATA-04, DATA-05, DATA-06
**UI hint:** yes
**Success Criteria:**

1. Admin upload PDF text, DOCX, CSV, XLSX, TXT, JSON/JSONL và .log vào dataset, xem nguồn/metadata và trạng thái xử lý; file/schema sai được báo lỗi.
2. Import log/ticket/incident/bảng theo schema công bố giữ ID, timestamp, hệ thống, trạng thái/ưu tiên và locator; người dùng mở đúng page/section/row/event/JSON record ở version nguồn tương ứng.
3. Retry/restart job không mất trạng thái hoặc nhân đôi canonical records; việc parse/chunk thực hiện ngoài request xử lý nặng của API.
4. Admin xóa/reprocess nguồn; chỉ version active được đọc và đưa vào index ở phase 3. Người mất quyền không xem/tải được nguồn qua API trực tiếp.
5. Loader/parser boundary trả nội dung và provenance mà không phụ thuộc LLM; OCR/format chưa hỗ trợ báo rõ và không đánh dấu ready sai.

**Plans:** TBD

### Phase 3: Grounded Knowledge Retrieval

**Goal:** Người dùng hỏi đáp tiếng Việt trên dữ liệu được cấp quyền và kiểm tra nguồn qua LangChain RAG, pgvector và hai OpenAI provider adapters độc lập.
**Mode:** mvp
**Depends on:** Phase 2
**Requirements:** RAG-01, RAG-02, RAG-03, RAG-04, RAG-05, SYS-02, SYS-03, SYS-05
**UI hint:** yes
**Success Criteria:**

1. Admin cấu hình OpenAI generation và embedding model phía backend; chunk/query được embedding và lưu pgvector với model/dimension/version. Provider interfaces độc lập và có fake adapter cho test; local/Gemini adapters hoàn chỉnh ngoài MVP.
2. Người dùng hỏi đáp tiếng Việt, lọc dataset/nguồn/hệ thống/thời gian và tìm đúng order ID/error/correlation ID; DH001 không bị lẫn DH010 khi kết hợp exact/lexical/dense retrieval.
3. Nhận định có evidence IDs hợp lệ và nguồn mở đúng đoạn/version; câu hỏi thiếu hoặc mâu thuẫn bằng chứng trả rõ giới hạn thay vì nguyên nhân chắc chắn.
4. ACL/active-source filters áp dụng trước mọi retrieval branch, context chỉ chứa bằng chứng được phép; response và history kiểm tra quyền hiện tại, không trả dữ liệu đã mất quyền trong quá trình request.
5. Context generation có token budget; secret fixtures được che trước embedding và generation egress; timeout/API errors hiển thị rõ, cloud tracing tắt mặc định và secrets không xuất hiện trên Web.

**Plans:** TBD

### Phase 4: Logistics Incident and Ticket Analysis

**Goal:** Kỹ thuật viên phân tích sự cố đồng bộ WMS–TMS từ log/ticket và nhận hướng kiểm chứng/xử lý có nguồn.
**Mode:** mvp
**Depends on:** Phase 3
**Requirements:** INC-01, INC-02, INC-03, INC-04, INC-05, EVAL-01
**UI hint:** yes
**Success Criteria:**

1. Kỹ thuật viên nhập mô tả sự cố/order ID hoặc nhập/upload ticket theo schema và nhận phân loại lỗi, hệ thống, ưu tiên đề xuất cùng bằng chứng.
2. Luồng DH001 liên kết log WMS/API/TMS theo ID/time và hiển thị trình tự sự kiện; không lẫn order gần giống hoặc incident cũ.
3. Kết quả tìm SOP/ticket/incident tương tự, phân biệt observation, precedent, giả thuyết nguyên nhân và cause đã xác nhận; nêu dữ liệu còn thiếu và bước kiểm chứng/xử lý.
4. Bộ dữ liệu mẫu bao phủ các format MVP, ticket/incident/log/SOP/bảng vận hành với ground truth và expected report metrics; chạy được luồng phân tích Web end-to-end.
5. Phân tích/lịch sử/citations chỉ trong phạm vi quyền; không gọi tools, gửi thông báo, cập nhật ticket hoặc thao tác WMS/TMS thật.

**Plans:** TBD

### Phase 5: On-Demand Incident Reports and PDF

**Goal:** Người dùng tạo báo cáo sự cố IT/logistics theo kỳ hoặc khoảng tùy chọn, kiểm tra số liệu/nguồn và tải PDF tiếng Việt.
**Mode:** mvp
**Depends on:** Phase 4
**Requirements:** REP-01, REP-02, REP-03, REP-04, REP-05, REP-06
**UI hint:** yes
**Success Criteria:**

1. Người dùng chọn ngày/tuần/tháng/custom interval và scope dataset; timezone và biên kỳ được công bố, dataset ngoài quyền bị từ chối qua API.
2. Số ticket và incident được đếm riêng; nhóm lỗi, ưu tiên, hệ thống, trạng thái và thời gian xử lý tính từ toàn bộ canonical records trong kỳ bằng query/rules xác định, khớp ground truth.
3. Báo cáo nêu cause đã xác nhận nếu có, trạng thái chưa biết và lỗi lặp theo grouping rule; nhận xét/đề xuất dùng evidence mà không sửa số liệu cố định.
4. Người dùng xem trước, mở provenance/snapshot và tải PDF tiếng Việt đọc được với bảng nhiều trang; Admin xem mọi báo cáo, Kỹ thuật viên chỉ xem phạm vi quyền hiện tại kể cả bản đã tạo.
5. Report Service độc lập, lưu kỳ/bộ lọc/source versions/metrics; mất quyền chặn history/PDF, lỗi LLM không được che bằng nhận xét giả. Chưa có scheduler hoặc tự gửi báo cáo.

**Plans:** TBD

### Phase 6: MVP Reliability and Acceptance

**Goal:** Nhóm dự án chứng minh MVP đáp ứng quyền, evidence, số liệu và recovery trên bộ đánh giá tái lập; người vận hành có hướng dẫn local và giới hạn đo được.
**Mode:** mvp
**Depends on:** Phase 5
**Requirements:** EVAL-02, EVAL-03
**UI hint:** yes
**Success Criteria:**

1. Bộ eval tái lập kiểm tra ID gần giống, evidence thiếu/mâu thuẫn, citation support và prompt injection; ghi kết quả và các lỗi còn lại, không dùng similarity như xác suất root cause.
2. Test trực tiếp API/source/history/PDF chứng minh không rò dữ liệu ngoài quyền, thu hồi quyền có hiệu lực và nguồn đã xóa không còn được truy xuất; retry/restart không nhân đôi records.
3. Report metrics/PDF khớp fixtures về duplicate, ticket–incident links, biên kỳ/timezone và incident đang mở; nhận xét và citations có evidence hỗ trợ.
4. Đo ingestion/retrieval/generation/report latency trên cấu hình máy/dataset công bố, ghi giới hạn thực tế và compatibility pins; không tuyên bố SLA/accuracy chưa đo.
5. Hướng dẫn Docker Compose, cấu hình secrets/providers, seed mẫu, recovery/reindex và nghiệm thu đủ để người vận hành chạy lại luồng Web → RAG → analysis → PDF.

**Plans:** TBD

## Coverage and Quality Gates

35/35 v1 requirements map exactly once. AUTH-04 được sở hữu phase 1, nhưng mọi chức năng thêm từ phase 2–5 phải có kiểm chứng quyền tại thời điểm triển khai; phase 6 là kiểm tra tổng hợp, không trì hoãn bảo mật đến cuối. Tương tự citations, retry và số liệu phải được test trong phase tạo chức năng.

Chi tiết models, parser packages, queue implementation, timezone/report rules và acceptance thresholds sẽ được cụ thể hóa trong discuss/plan phase. Dependency graph ở roadmap là tuần tự; parallelization áp dụng các plans độc lập bên trong phase, không vượt gate phụ thuộc.

## Progress

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Local Workspace and Access Control | 1/5 | In Progress|  |
| 2. Dataset Ingestion and Source Lifecycle | 0/TBD | Not started | - |
| 3. Grounded Knowledge Retrieval | 0/TBD | Not started | - |
| 4. Logistics Incident and Ticket Analysis | 0/TBD | Not started | - |
| 5. On-Demand Incident Reports and PDF | 0/TBD | Not started | - |
| 6. MVP Reliability and Acceptance | 0/TBD | Not started | - |

---
*Created: 2026-10-03 under the user-authorized automatic workflow. No implementation plans or code executed yet.*

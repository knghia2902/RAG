# Modular RAG cho IT & Logistics

## What This Is

Ứng dụng Web RAG cho môi trường doanh nghiệp logistics, hỗ trợ kỹ thuật viên phân tích log/sự cố, xử lý ticket IT và tạo báo cáo sự cố IT kết hợp sự cố hệ thống logistics. MVP sử dụng dữ liệu mẫu, tổng hợp bằng chứng từ log, ticket, SOP và dữ liệu vận hành để đưa ra phân tích, đề xuất và nguồn trích dẫn có thể kiểm tra.

Backend được thiết kế theo API, tách RAG Core và LLM Provider để sau này kết nối MCP hoặc phát triển AI Agent. Giai đoạn MVP chỉ phân tích và đề xuất, chưa thực hiện hành động trên hệ thống thật.

Stack đã chốt: Python + FastAPI, LangChain, PostgreSQL + pgvector, OpenAI Embeddings, OpenAI API cho generation, Next.js + TypeScript và Docker Compose. Embedding Provider và LLM Provider tách riêng để thay model local hoặc Gemini sau này.

## Core Value

Kỹ thuật viên có thể tìm bằng chứng liên quan và nhận phân tích, đề xuất xử lý sự cố logistics kèm nguồn trích dẫn để kiểm tra lại.

## Requirements

### Validated

- Admin/Kỹ thuật viên đăng nhập và đăng xuất; tài khoản bị vô hiệu hóa mất quyền truy cập API; Admin tạo, cập nhật role, đặt lại mật khẩu và vô hiệu hóa tài khoản — Phase 1 (AUTH-01, AUTH-02).
- Admin cấp/thu hồi quyền dataset; Kỹ thuật viên mặc định không có quyền và chỉ thấy dataset được cấp — Phase 1 (AUTH-03).
- Local Docker Compose runtime với PostgreSQL + pgvector, dữ liệu bền vững qua restart và giao diện chỉ publish trên loopback — Phase 1 (SYS-01).
- Web gọi FastAPI theo contract; module/provider boundary và policy seam có thể mở rộng — Phase 1 (SYS-04).
- Policy contract cho nguồn, lịch sử kết quả và báo cáo được xác định cho các module sau; endpoint thực tế và kiểm tra quyền tại các endpoint đó vẫn là phần việc của các phase tương ứng — Phase 1 slice (AUTH-04, AUTH-05).
- Ingestion tài liệu đa định dạng, quản lý vòng đời nguồn/phiên bản, xem trước trích đoạn có tọa độ nguồn — Phase 2 (DATA-01 đến DATA-06).
- Truy xuất tri thức có bằng chứng trích dẫn inline, phân biệt mã định danh chính xác (DH001 vs DH010), lọc phạm vi và Live Scope Recheck — Phase 3 (RAG-01 đến RAG-05, SYS-02).
- Phân tích sự cố logistics đa hệ thống WMS/API/TMS theo mã đơn hàng, cô lập điểm đứt gãy đồng bộ đầu tiên, upload ticket kiểm định schema nghiêm ngặt theo dòng, phân loại P1-P4, phân định nguyên nhân vs giả thuyết, cảnh báo thiếu log (RAG-05), dẫn chứng quy trình SOP-LOG-01 và Live Scope Recheck thời gian thực — Phase 4 (INC-01, INC-02, INC-03, INC-04, INC-05, EVAL-01, AUTH-04).
- Báo cáo sự cố IT & Logistics theo yêu cầu theo ngày/tuần/tháng/tùy chọn trong scope dataset múi giờ Asia/Ho_Chi_Minh; tính toán 100% tất định từ canonical records (không từ context top-k); đếm độc lập ticket và incident; MTTR tính riêng cho sự cố đã đóng; phát hiện lỗi lặp lại (System + Error Group >= 2); tổng hợp narrative LLM với mask_secrets và fallback SYS-05; xuất PDF chuẩn in A4 tiếng Việt WeasyPrint 70.0; và Live Scope Recheck từ chối HTTP 403 nếu quyền bị thu hồi — Phase 5 (REP-01 đến REP-06, EVAL-03).

### Active

- [ ] Admin upload/quản lý tài liệu và dataset, theo dõi ingestion, cấu hình provider và xem báo cáo.
- [ ] Kỹ thuật viên tra cứu/phân tích bằng RAG và tạo/xem báo cáo trong phạm vi dataset được cấp.
- [ ] Áp dụng và kiểm thử policy hiện hành trên các endpoint nguồn, truy xuất, lịch sử và báo cáo/PDF khi những module đó được triển khai.
- [ ] Parser hỗ trợ PDF có text, DOCX, CSV, XLSX, TXT, JSON/JSONL và .log; tách module để thêm OCR sau này.
- [ ] Người dùng upload và quản lý dữ liệu/tài liệu trên Web.
- [ ] Lập chỉ mục các nguồn dữ liệu phù hợp để truy xuất bằng RAG.
- [ ] Phân tích log và sự cố, liên kết thông tin theo mã đơn hàng/API/hệ thống liên quan.
- [ ] Nhập hoặc upload ticket IT để phân loại vấn đề, tìm log, SOP và incident/ticket tương tự.
- [ ] Tổng hợp nguyên nhân có khả năng xảy ra và đề xuất các bước xử lý dựa trên bằng chứng.
- [ ] Hỏi đáp dựa trên dữ liệu được lập chỉ mục.
- [ ] Hiển thị tài liệu và đoạn dữ liệu được sử dụng trong câu trả lời/phân tích.
- [x] Tạo báo cáo sự cố IT kết hợp sự cố hệ thống logistics theo yêu cầu, chọn kỳ ngày/tuần/tháng hoặc khoảng thời gian tùy chọn và xuất PDF.
- [x] Report Service tách riêng để bổ sung scheduler và gửi báo cáo định kỳ sau này.
- [x] Báo cáo gồm tổng số ticket/sự cố, nhóm lỗi, ưu tiên, hệ thống liên quan, nguyên nhân nếu xác định được, trạng thái, thời gian phát sinh/xử lý, lỗi lặp lại, đề xuất và nguồn dữ liệu.
- [ ] Database, vector database và dữ liệu RAG ưu tiên chạy local.
- [ ] Tách LLM Provider và Embedding Provider; MVP dùng OpenAI API, hỗ trợ thay Gemini/local generation và local embedding sau này.
- [ ] Chỉ gửi context liên quan được RAG truy xuất tới LLM, không gửi nguyên tài liệu không cần thiết.
- [ ] Backend cung cấp API để phục vụ Web và tạo nền tảng cho MCP/AI Agent sau này.

### Out of Scope

- OCR/PDF scan/hình ảnh — mở rộng qua parser adapter sau MVP.
- Scheduler và tự động gửi báo cáo định kỳ — mở rộng Report Service sau MVP.
- MCP server/adapter — chuẩn bị backend API, triển khai ở giai đoạn mở rộng.
- Kết nối trực tiếp WMS, TMS, ticket và monitoring thật trong MVP — dữ liệu mẫu đủ để kiểm chứng luồng ban đầu.
- AI Agent tự gọi tools hoặc thực hiện thao tác — phát triển sau khi RAG hoạt động ổn định.
- Chạy lại đồng bộ, cập nhật/đóng ticket thật, kiểm tra API thật hoặc gửi thông báo tự động — thuộc giai đoạn Agent, cần phân quyền và phê duyệt hành động ảnh hưởng hệ thống.
- Xuất báo cáo Excel và Word — bổ sung sau PDF.
- Bắt buộc chạy LLM hoàn toàn nội bộ trong MVP — trước mắt cho phép API ngoài, giữ khả năng thay provider.

## Context

### Người dùng và tình huống điển hình

Người dùng mục tiêu là kỹ thuật viên/nhân viên IT hỗ trợ hệ thống logistics. Ví dụ đơn hàng DH001 đã được xử lý trong WMS nhưng chưa xuất hiện hoặc chưa cập nhật trạng thái trong TMS.

Quy trình hiện tại được giả lập: phát hiện lỗi → kiểm tra log → tìm mã đơn hàng/API liên quan → tra tài liệu kỹ thuật → tìm sự cố tương tự → xác định nguyên nhân → đưa ra cách xử lý → ghi lại kết quả trong ticket/báo cáo. RAG hỗ trợ tìm kiếm và tổng hợp thông tin trong quy trình này.

Khi nhận ticket “Đơn hàng DH001 không đồng bộ từ WMS sang TMS”, hệ thống cần phân loại vấn đề, tìm log liên quan, tìm SOP và incident/ticket tương tự, tổng hợp nguyên nhân có khả năng xảy ra và đề xuất bước xử lý kèm nguồn để kỹ thuật viên xác minh.

### Dữ liệu mẫu

- Log WMS/TMS/API.
- Ticket IT cũ và ticket được nhập/upload.
- PDF/Word chứa SOP và hướng dẫn xử lý sự cố.
- CSV/Excel chứa dữ liệu đơn hàng và vận chuyển.
- Lịch sử incident và cách xử lý.
- Dữ liệu phục vụ báo cáo ngày/tuần/tháng.

### Báo cáo ưu tiên

Báo cáo đầu tiên kết hợp sự cố IT và sự cố hệ thống logistics, gồm số ticket/sự cố, phân loại nhóm lỗi, mức ưu tiên, WMS/TMS/API/Database liên quan, nguyên nhân nếu xác định được, tình trạng xử lý, thời gian phát sinh và xử lý, lỗi thường xuyên lặp lại, đề xuất và nguồn dữ liệu. PDF là định dạng xuất đầu tiên.

### Hướng phát triển kiến trúc

MVP: Next.js Web → FastAPI → LangChain RAG Core → LLM Provider → phân tích/đề xuất/nguồn trích dẫn.

Ingestion/retrieval: Tài liệu/Log/Ticket → Loader → Chunking → Embedding Provider (OpenAI) → pgvector → Retriever → LLM → kết quả + nguồn. PostgreSQL lưu thêm bản ghi có cấu trúc để tính số liệu báo cáo.

Giai đoạn sau: Web / MCP → RAG Core → LLM → AI Agent → Tools / WMS, TMS, Ticket, Monitoring. Agent có thể kiểm tra API, chạy lại đồng bộ, tạo/cập nhật ticket, gửi thông báo hoặc automation; hành động ảnh hưởng hệ thống cần phân quyền và người phụ trách phê duyệt.

### Cấu trúc dự án đã chốt

```text
RAG/
  backend/
    app/
      api/
      rag/          # Loader, Chunker, Embedding Provider, Retriever, Vector Store
      llm/          # LLM Provider
      modules/
        log_analysis/
        tickets/
        reports/
      database/
      auth/
      main.py
    tests/
    scripts/
  frontend/         # Next.js + TypeScript
  data/
    sample/
    uploads/
  storage/
  docs/
  docker-compose.yml
```

Worker/job runner có thể dùng cùng backend image, entrypoint tách khỏi API; không bắt buộc thêm top-level app. LangChain đóng vai trò pipeline/adapters trong rag/; auth, database và các module nghiệp vụ không phụ thuộc trực tiếp chi tiết chain.

## Constraints

- **Deployment**: Docker Compose; PostgreSQL + pgvector, file nguồn và dữ liệu RAG chạy local.
- **LLM**: OpenAI API trong MVP, LLM Provider độc lập để hỗ trợ Gemini/local sau này; generation model cụ thể chưa chốt.
- **Embedding**: OpenAI Embeddings trong MVP qua Embedding Provider; model/dimension cấu hình và lưu theo index version. Local embedding dành cho mở rộng.
- **Data exposure**: Generation chỉ gửi context liên quan được truy xuất. Ingestion gửi các chunk cần index và retrieval gửi query cho OpenAI Embeddings; áp dụng che secret/giới hạn input cho cả hai đường API. Không gửi file nguyên bản không cần thiết; lưu trữ local không có nghĩa mọi xử lý AI đều local.
- **Authority**: MVP chỉ phân tích và đề xuất, không thực hiện thao tác trên hệ thống thật.
- **Evidence**: Kết quả phân tích và báo cáo phải có nguồn dữ liệu để kiểm tra lại.
- **Scope**: RAG trước, AI Agent sau; nguồn dữ liệu thật chưa bắt buộc trong MVP.
- **Access control**: Admin/Kỹ thuật viên; kỹ thuật viên chỉ truy xuất và tạo/xem báo cáo trong phạm vi được cấp quyền. Đề xuất dataset là đơn vị cấp quyền MVP; cần xác nhận cùng yêu cầu.
- **Formats**: PDF có text, DOCX, CSV, XLSX, TXT, JSON/JSONL, .log; không OCR trong MVP.
- **Reporting**: Theo yêu cầu với kỳ ngày/tuần/tháng hoặc khoảng thời gian tùy chọn; không scheduler trong MVP.
- **Open decisions**: Generation/embedding model cụ thể, package pins, queue implementation, quy mô dữ liệu, chỉ tiêu đánh giá, thời gian và ngân sách. Đơn vị cấp quyền dataset là baseline thiết kế có thể điều chỉnh trước triển khai.

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| RAG trước, AI Agent sau | Kiểm chứng truy xuất và tổng hợp bằng chứng trước khi thêm hành động | — Pending |
| Web MVP với backend API | Có giao diện sử dụng và nền tảng tích hợp MCP/Agent | — Pending |
| Dùng dữ liệu mẫu trong MVP | Không phụ thuộc kết nối hệ thống doanh nghiệp thật | — Pending |
| Dữ liệu và database ưu tiên local | Phù hợp hướng triển khai nội bộ doanh nghiệp | — Pending |
| Tách LLM Provider | Dễ chuyển API ngoài sang model local | — Pending |
| Chỉ gửi context liên quan cho LLM | Giới hạn dữ liệu truyền ra ngoài | — Pending |
| Nguồn trích dẫn trong phân tích và báo cáo | Kỹ thuật viên kiểm tra căn cứ của kết quả | — Pending |
| PDF trước, Excel/Word sau | Tập trung định dạng báo cáo MVP đã ưu tiên | — Pending |
| Hai role Admin/Kỹ thuật viên, mô hình quyền mở | Đáp ứng MVP và thêm vai trò khi triển khai thực tế | — Pending |
| Parser module riêng, chưa OCR | Thêm format/OCR mà không thay RAG Core | — Pending |
| Report Service riêng, chưa scheduler | Thêm chạy/gửi báo cáo định kỳ ở giai đoạn sau | — Pending |
| FastAPI + LangChain + Next.js/TypeScript | Stack do người dùng chốt cho Modular RAG | — Pending |
| PostgreSQL + pgvector | Gộp relational và vector storage local; thay đề xuất Qdrant ban đầu | — Pending |
| OpenAI Embeddings + OpenAI LLM API | Đơn giản hóa MVP; tách hai provider để thay về sau | — Pending |
| Docker Compose và cấu trúc backend/app/modules | Đóng gói local và giữ module nghiệp vụ rõ ràng | — Pending |

## Evolution

Tài liệu được cập nhật khi chuyển phase và kết thúc milestone.

Sau mỗi phase: chuyển yêu cầu đã kiểm chứng sang Validated; chuyển yêu cầu không còn phù hợp sang Out of Scope kèm lý do; thêm yêu cầu mới; ghi quyết định; kiểm tra lại mô tả sản phẩm.

Sau mỗi milestone: rà soát toàn bộ tài liệu, giá trị cốt lõi, phạm vi loại trừ và bối cảnh sử dụng thực tế.

---
*Last updated: 2026-10-14 after Phase 5 on-demand incident reports and PDF verification.*

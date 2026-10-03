# Logistics IT RAG

## What This Is

Ứng dụng Web RAG cho môi trường doanh nghiệp logistics, hỗ trợ kỹ thuật viên phân tích log/sự cố, xử lý ticket IT và tạo báo cáo sự cố IT kết hợp sự cố hệ thống logistics. MVP sử dụng dữ liệu mẫu, tổng hợp bằng chứng từ log, ticket, SOP và dữ liệu vận hành để đưa ra phân tích, đề xuất và nguồn trích dẫn có thể kiểm tra.

Backend được thiết kế theo API, tách RAG Core và LLM Provider để sau này kết nối MCP hoặc phát triển AI Agent. Giai đoạn MVP chỉ phân tích và đề xuất, chưa thực hiện hành động trên hệ thống thật.

## Core Value

Kỹ thuật viên có thể tìm bằng chứng liên quan và nhận phân tích, đề xuất xử lý sự cố logistics kèm nguồn trích dẫn để kiểm tra lại.

## Requirements

### Validated

Chưa có — cần triển khai và kiểm chứng MVP.

### Active

- [ ] Người dùng upload và quản lý dữ liệu/tài liệu trên Web.
- [ ] Lập chỉ mục các nguồn dữ liệu phù hợp để truy xuất bằng RAG.
- [ ] Phân tích log và sự cố, liên kết thông tin theo mã đơn hàng/API/hệ thống liên quan.
- [ ] Nhập hoặc upload ticket IT để phân loại vấn đề, tìm log, SOP và incident/ticket tương tự.
- [ ] Tổng hợp nguyên nhân có khả năng xảy ra và đề xuất các bước xử lý dựa trên bằng chứng.
- [ ] Hỏi đáp dựa trên dữ liệu được lập chỉ mục.
- [ ] Hiển thị tài liệu và đoạn dữ liệu được sử dụng trong câu trả lời/phân tích.
- [ ] Tạo báo cáo sự cố IT kết hợp sự cố hệ thống logistics theo kỳ ngày/tuần/tháng và xuất PDF.
- [ ] Báo cáo gồm tổng số ticket/sự cố, nhóm lỗi, ưu tiên, hệ thống liên quan, nguyên nhân nếu xác định được, trạng thái, thời gian phát sinh/xử lý, lỗi lặp lại, đề xuất và nguồn dữ liệu.
- [ ] Database, vector database và dữ liệu RAG ưu tiên chạy local.
- [ ] Tách LLM Provider, cho phép dùng API ngoài trong MVP và thay bằng model local sau này.
- [ ] Chỉ gửi context liên quan được RAG truy xuất tới LLM, không gửi nguyên tài liệu không cần thiết.
- [ ] Backend cung cấp API để phục vụ Web và tạo nền tảng cho MCP/AI Agent sau này.

### Out of Scope

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

MVP: Web → API → RAG Core → LLM Provider → phân tích/đề xuất/nguồn trích dẫn.

Giai đoạn sau: Web / MCP → RAG Core → LLM → AI Agent → Tools / WMS, TMS, Ticket, Monitoring. Agent có thể kiểm tra API, chạy lại đồng bộ, tạo/cập nhật ticket, gửi thông báo hoặc automation; hành động ảnh hưởng hệ thống cần phân quyền và người phụ trách phê duyệt.

## Constraints

- **Deployment**: Database, vector database và dữ liệu RAG ưu tiên local; phương án đóng gói/chạy cụ thể chưa chốt.
- **LLM**: Cho phép API ngoài trong MVP nhưng phải có abstraction provider để hỗ trợ model local hoặc server nội bộ sau này.
- **Data exposure**: Chỉ gửi context liên quan được truy xuất, không gửi nguyên file/tài liệu không cần thiết.
- **Authority**: MVP chỉ phân tích và đề xuất, không thực hiện thao tác trên hệ thống thật.
- **Evidence**: Kết quả phân tích và báo cáo phải có nguồn dữ liệu để kiểm tra lại.
- **Scope**: RAG trước, AI Agent sau; nguồn dữ liệu thật chưa bắt buộc trong MVP.
- **Open decisions**: Chưa chốt tech stack, LLM/embedding provider, xác thực/phân quyền MVP, quy mô dữ liệu, chỉ tiêu đánh giá, thời gian và ngân sách.

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

## Evolution

Tài liệu được cập nhật khi chuyển phase và kết thúc milestone.

Sau mỗi phase: chuyển yêu cầu đã kiểm chứng sang Validated; chuyển yêu cầu không còn phù hợp sang Out of Scope kèm lý do; thêm yêu cầu mới; ghi quyết định; kiểm tra lại mô tả sản phẩm.

Sau mỗi milestone: rà soát toàn bộ tài liệu, giá trị cốt lõi, phạm vi loại trừ và bối cảnh sử dụng thực tế.

---
*Last updated: 2026-10-03 after project definition approved by user.*

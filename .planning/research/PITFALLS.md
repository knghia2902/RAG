# Pitfalls Research

**Researched:** 2026-10-03
**Confidence:** HIGH về failure modes cơ bản; MEDIUM về biện pháp cụ thể chưa kiểm thử.

## Critical Pitfalls and Phase Mapping

Tên phase dưới đây là năng lực dự kiến, chưa phải phase roadmap đã chốt.

| Failure mode | Dấu hiệu | Phòng tránh và kiểm chứng | Năng lực cần xử lý |
|---|---|---|---|
| Vector-only nhầm DH001/DH010 | Log cùng ngữ nghĩa nhưng sai order ID | Exact entity branch; eval near-collision IDs, error codes và correlation IDs | Retrieval |
| Cắt mất context log/SOP | Có exception nhưng thiếu request hoặc bước điều kiện | Chunk theo section/event window; giữ timestamp và parent locators | Ingestion |
| Citation có tên file nhưng không chứng minh claim | Link tồn tại nhưng đoạn nguồn không liên quan | Server kiểm tra evidence ID; eval claim support và click-to-source | Grounded answers |
| LLM tính tổng từ top-k | PDF thiếu ticket hoặc tổng thay đổi giữa hai lần | DB aggregates trên toàn bộ scope; snapshot và expected metrics fixture | Reporting |
| Đếm trùng ticket/incident | Một sự cố có nhiều ticket bị coi là nhiều incident | Đếm riêng tickets/incidents, liên kết ID, công bố grouping rules | Canonical data/reporting |
| Lệch kỳ và thời gian xử lý | Sự cố sát nửa đêm sang kỳ khác; duration âm | UTC storage, timezone báo cáo rõ, interval [start,end), missing resolved_at không thành 0 | Structured import/reporting |
| Log sự cố hiện tại bị incident cũ lấn át | Kết luận từ lần trước dù mã lỗi hiện tại khác | Time/system/entity filters; tách evidence hiện tại và precedent | Incident analysis |
| Tương đồng bị diễn giải là nguyên nhân chắc chắn | Luôn có root cause dù thiếu log | Schema observation/hypothesis/confirmed cause; eval thiếu/mâu thuẫn | Incident analysis |
| Xóa/reindex nhưng nguồn cũ còn xuất hiện | UI đã xóa nhưng RAG vẫn cite | Version activation, tombstone, reconciliation và query active-state check | Data lifecycle |
| Job mất hoặc nhân đôi sau restart | Index kẹt processing hoặc duplicate records | Persist state, retry giới hạn, deterministic IDs/checksum, recovery test | Ingestion/worker |
| Đổi embedding nhưng giữ index cũ | Dimension mismatch hoặc recall giảm | Store model revision/dimension; rebuild versioned collection | Retrieval operations |

## Data and Security Boundaries

Log/ticket/SOP là dữ liệu không đáng tin cậy: có thể chứa nội dung yêu cầu bỏ qua chỉ dẫn. Tách instruction và evidence, không cấp tools, validation output và kiểm tra bằng fixture prompt injection. Các biện pháp này giảm rủi ro, không bảo đảm loại bỏ mọi injection. Cơ sở: [OWASP prompt injection guidance](https://cheatsheetseries.owasp.org/cheatsheets/LLM_Prompt_Injection_Prevention_Cheat_Sheet.html).

Chỉ truy xuất ít context chưa đủ bảo đảm không gửi secret: cần rules redaction cho token/password/key trước egress, không log full prompt mặc định, ghi metadata request và nguồn đã chọn. Chưa chọn provider nên retention policy, pricing và model cụ thể chưa được xác minh.

PDF dùng template do server quản lý, escape output; chặn arbitrary network/file fetch và giới hạn tài nguyên. WeasyPrint mô tả rủi ro với HTML/CSS không tin cậy: [tài liệu bảo mật](https://doc.courtbouillon.org/weasyprint/stable/first_steps.html#security).

Nếu scope chọn nhiều tài khoản/phòng ban, kiểm soát quyền phải có trên truy vấn DB, vector filters, source viewer và download; chỉ lọc trong UI là không đủ. Với local demo một workspace, không tự quảng bá là đã có bảo mật enterprise đầy đủ.

## Technical Debt and Performance

- Toàn bộ log thành một chunk: nhanh viết nhưng khó correlate/trích nguồn; dùng events/windows.
- Embedding mọi dòng INFO lặp: tăng chi phí index; giữ canonical logs đầy đủ, chọn cửa sổ/index policy và benchmark.
- OCR mặc định mọi PDF: ingestion chậm và mất mã; bắt đầu PDF text nếu scope cho phép, OCR chỉ khi cần.
- Không có source version: citation không thể tái lập; ghi immutable locator trước launch.
- Benchmark chỉ fixture sạch: chất lượng demo không phản ánh lỗi; thêm ID gần giống, timezone, duplicate, malformed files và thiếu evidence.

## Looks Done But Isn't

- [ ] DH001 lấy đúng log; DH010 không bị lẫn.
- [ ] Câu hỏi không có đáp án trả thiếu evidence thay vì bịa.
- [ ] Mỗi citation mở đúng page/section/row/log event và version.
- [ ] Tổng số/duration PDF khớp fixture SQL, kể cả duplicate, open incident và biên kỳ.
- [ ] Xóa nguồn không còn được dùng; restart không mất job hoặc nhân đôi dữ liệu.
- [ ] Lỗi provider/timeout hiển thị rõ; secrets mẫu không ra context.
- [ ] PDF tiếng Việt đúng font, bảng nhiều trang đọc được.

## Recovery Strategies

Sai index: vô hiệu version bị lỗi, sửa parser/model và rebuild từ canonical source. Sai báo cáo: tạo snapshot mới và đánh dấu bản cũ, không sửa âm thầm metrics đã xuất. Sai hypothesis: giữ evidence, sửa prompt/retrieval và thêm regression case. Quy trình khôi phục cần được thử trên fixture trước nghiệm thu.

## Sources

- [PROJECT.md](../PROJECT.md), [Qdrant filters](https://qdrant.tech/documentation/search/filtering/), [BGE-M3](https://huggingface.co/BAAI/bge-m3), [OWASP](https://cheatsheetseries.owasp.org/cheatsheets/LLM_Prompt_Injection_Prevention_Cheat_Sheet.html), [WeasyPrint security](https://doc.courtbouillon.org/weasyprint/stable/first_steps.html#security).
- Các failure modes logistics/reporting là suy luận thiết kế từ use case, không phải postmortem đã quan sát trong hệ thống thật.

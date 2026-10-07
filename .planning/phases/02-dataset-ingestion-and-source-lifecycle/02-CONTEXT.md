# Phase 2: Dataset Ingestion and Source Lifecycle - Context

**Gathered:** 2026-10-07  
**Status:** Ready for planning

<domain>
## Phase Boundary

Admin quản lý dataset và nạp các file PDF có text, DOCX, CSV, XLSX, TXT, JSON/JSONL và `.log` qua Web. Backend kiểm tra định dạng/schema, lưu file ở storage riêng tư local, parse/chuẩn hóa dữ liệu, giữ version và provenance, lưu trạng thái/lỗi job có thể phục hồi, cho phép retry/reprocess/xóa và cung cấp đoạn nguồn có locator cho người đang có quyền dataset.

Phase này tạo dữ liệu chuẩn và đoạn nội dung có provenance để phase 3 lập chỉ mục. Không tạo embedding/vector index, không gọi LLM/OpenAI, không triển khai retrieval/chat, phân tích ticket/sự cố hay báo cáo. Không OCR; file scan và định dạng không hỗ trợ phải báo lỗi rõ, không được hiện là `ready`. Không dùng nguồn production thật hoặc thực hiện thao tác trên WMS/TMS.
</domain>

<decisions>
## Implementation Decisions

### Upload và version nguồn

- **D-01:** Upload nhiều file có kết quả riêng theo từng file. Trong cùng dataset, nội dung có cùng checksum là no-op idempotent; nội dung thay đổi dưới cùng tên file tạo source version bất biến mới. Reprocess chạy lại trên cùng version, không tạo version mới.
- **D-02:** Version đang active tiếp tục được dùng trong khi version mới được parse/kiểm tra. Chỉ chuyển active khi toàn bộ bước bắt buộc của version mới thành công; lỗi giữ nguyên version active cũ. Cùng một batch có thể có kết quả thành công/thất bại riêng theo file, nhưng không được kích hoạt một phần của một version.

### Schema và lỗi import

- **D-03:** Admin chọn source profile đã công bố trước import (ví dụ: tài liệu chung, log, ticket, incident hoặc bảng vận hành); giao diện cho xem profile, trường kỳ vọng và preview trước khi xác nhận. Chọn profile xác định cách diễn giải dữ liệu nghiệp vụ; không âm thầm đoán schema từ extension/header.
- **D-04:** Parser validation xác định và trả vị trí lỗi theo row/record cùng lý do. Lỗi trường bắt buộc hoặc cấu trúc làm version mới thất bại nguyên tử và không active; dữ liệu hợp lệ có thể được đếm để chẩn đoán nhưng không được xuất hiện như nguồn hoàn chỉnh/ready. Cảnh báo về trường tùy chọn có thể hiển thị mà không chặn khi schema cho phép. Quy tắc bắt buộc/tùy chọn phải được công bố theo profile.
- **D-05:** Schema chuẩn hóa phải giữ ID, hệ thống, trạng thái/ưu tiên, timestamp và locator theo DATA-06. Parser trả nội dung chuẩn cùng provenance, độc lập LLM/provider. Không xóa dữ liệu gốc/canonical của version active chỉ vì lần reprocess thất bại.

### Tiến trình và retry

- **D-06:** Parse và chuẩn hóa chạy dưới durable background job, không giữ request upload mở cho công việc nặng. Trạng thái theo từng nguồn được lưu bền vững và hiển thị sau reload/restart; tối thiểu gồm queued, processing, ready và failed, kèm lỗi có thể xử lý.
- **D-07:** Job retry phải idempotent và có giới hạn. Lỗi tạm thời có thể retry giới hạn; sau trạng thái failed, Admin có thể chủ động retry. Retry/restart không nhân đôi canonical records và không làm version lỗi thành active. Cơ chế hàng đợi, backoff và cập nhật UI cụ thể do research/planning quyết định trong stack đã chọn.

### Xem nguồn và xóa

- **D-08:** Người dùng có quyền hiện tại trên dataset xem đoạn nội dung đã parse cùng source version và locator chính xác (page/section, sheet/row, JSON record/path hoặc log event/line). Response không để lộ đường dẫn filesystem hay public/static URL; file gốc giữ trong storage riêng tư. Giao diện MVP ưu tiên parsed preview; nếu có endpoint trả bytes file thì endpoint đó phải áp dụng cùng policy hiện tại.
- **D-09:** Chỉ version active được đọc như nguồn nội dung và có thể đưa vào index ở phase 3. Mọi lần đọc/preview kiểm tra lại quyền dataset hiện tại và trạng thái active ở backend; ẩn nút trên UI không thay thế authorization.
- **D-10:** Xóa lập tức tombstone nguồn/version và fence job đang chạy để nội dung không còn được liệt kê/đọc/index hoặc tái kích hoạt; dọn file và dữ liệu dẫn xuất sau đó. Reprocess dùng lại version hiện có. Mất quyền dataset cũng chặn việc đọc nguồn ngay từ API.

### the agent's Discretion

- Đề xuất tên, trường bắt buộc/tùy chọn, quy tắc timestamp và ví dụ của từng profile chuẩn hóa sao cho DATA-06 có thể nghiệm thu; schemas phải được công bố trước khi import.
- Chọn parser/library, cách biểu diễn PDF/DOCX/bảng/log, ranh giới chunk/excerpt, giới hạn kích thước file/batch/thời gian/tài nguyên, pagination và mức chi tiết tiến trình.
- Chọn queue/broker, schema persistence, backoff, lease/recovery, cleanup/reconciliation và cơ chế fencing cụ thể; giữ các job bền vững, bounded, idempotent và version-safe như các quyết định trên.
- Chọn UI upload/preview/status/retry/reprocess/delete chi tiết theo pattern hiện có của trang Dataset tiếng Việt.
- Chọn cách xử lý duplicate checksum khi tên file khác nhưng dataset giống nhau, miễn semantics hash-idempotency, provenance và hành vi UI rõ ràng.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Scope and acceptance
- `.planning/PROJECT.md` — sản phẩm, stack, giới hạn dữ liệu và quyền.
- `.planning/REQUIREMENTS.md` § Data and Document Management — DATA-01–DATA-06.
- `.planning/ROADMAP.md` § Phase 2: Dataset Ingestion and Source Lifecycle — phase boundary và success criteria.
- `.planning/config.json` — quy trình GSD, mức chi tiết, Git và tự động hóa.
- `.planning/phases/01-local-workspace-and-access-control/01-CONTEXT.md` — role, dataset ACL, localhost, UI tiếng Việt và các quyết định mang sang từ phase 1.

### Data contracts and security
- `docs/security-contracts.md` — kiểm tra quyền API nguồn, version active, private storage và yêu cầu kiểm thử trực tiếp endpoint.
- `backend/app/rag/contracts.py` — `SourceLocator`, `EvidenceChunk` và parser/chunker/provider-free contracts hiện có.
- `backend/app/auth/policy.py` — capability và dataset authorization hiện có.
- `backend/app/database/models.py` — model persistence hiện có.
- `backend/app/api/schemas.py` — pattern DTO/API hiện có.
- `backend/app/api/datasets.py` — route và policy pattern cho dataset.
- `backend/app/database/datasets.py` — truy vấn/lưu metadata dataset hiện có.
- `frontend/src/lib/contracts.ts` — frontend API contracts hiện có.
- `frontend/src/app/(workspace)/datasets/page.tsx` — pattern UI quản lý Dataset hiện có.

### Research
- `.planning/research/STACK.md` — baseline parser/worker/database và compatibility gates; kiểm tra/pin lại dependencies khi triển khai.
- `.planning/research/ARCHITECTURE.md` — source/version/job/provenance model và lifecycle gợi ý.
- `.planning/research/PITFALLS.md` — retry/restart, duplicate, version activation và provenance failure modes.

Không có SPEC.md, ADR bên ngoài, decisions index hoặc packaged spike/sketch findings cho Phase 2.
</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `backend/app/rag/contracts.py`: provider-free `Parser` nhận bytes/locator/dataset và trả các `EvidenceChunk`; `SourceLocator` có source/version cùng page, section, sheet, row, event và record.
- `backend/app/auth/policy.py`, `backend/app/api/dependencies.py` và `docs/security-contracts.md`: backend-owned identity/capability/dataset scope; nguồn mới phải dùng policy này thay vì nhận scope từ browser.
- `backend/app/api/datasets.py`, `backend/app/database/datasets.py`, `backend/app/api/schemas.py`: pattern route/service/DTO cho dataset metadata.
- `frontend/src/app/(workspace)/datasets/page.tsx` và `frontend/src/lib/contracts.ts`: trang Dataset hiện tại và frontend contract để mở rộng quản lý nguồn.

### Established Patterns
- Modular monolith FastAPI; route gọi service; SQLAlchemy/PostgreSQL là nguồn chuẩn. Web dùng Next.js/TypeScript và giao diện tiếng Việt.
- Dataset là đơn vị ACL; Admin quản lý repository. Kỹ thuật viên chỉ xem nội dung nguồn của dataset được cấp quyền.
- Storage phải private/local; backend kiểm tra quyền ở từng response. Source locator và version là một phần của evidence, không phải tùy chọn hiển thị.
- Repo hiện chưa có upload/source-version/job/parser implementation. Phase 2 thiết lập lifecycle; vector embeddings và retrieval thuộc Phase 3.

### Integration Points
- `backend/app/rag/`: parser/normalizer boundary, source locator, evidence excerpts/chunks, không phụ thuộc LLM.
- `backend/app/database/` và migration layer: source/version, import job, canonical records và lỗi/locator bền vững.
- `backend/app/api/`: admin upload/list/detail/retry/reprocess/delete và permission-checked source preview.
- `backend/app/auth/policy.py`: repository capability Admin-only và source read theo grant hiện tại.
- `frontend` Dataset workspace: upload theo dataset/profile, bảng nguồn, preview provenance, job status, lỗi và thao tác lifecycle.
- `storage/` và `docker-compose.yml`: volume file riêng tư và worker chạy cùng môi trường local.
</code_context>

<specifics>
## Specific Ideas

- Upload batch hiển thị kết quả riêng cho từng file; cùng checksum không tạo dữ liệu lặp, file thay đổi tạo version mới và version cũ còn active tới khi version mới hợp lệ.
- Log/ticket/incident/bảng phải có profile/schema công bố trước import; lỗi ghi rõ row/record để Admin sửa nguồn.
- Nguồn xem được phải mở đúng đoạn và locator trong đúng source version; sau khi xóa hoặc mất quyền thì request tiếp theo bị chặn.
- Không yêu cầu API key AI để upload/parse; Phase 2 không gửi file/chunk/query tới OpenAI hoặc LLM.
</specifics>

<deferred>
## Deferred Ideas

Không phát sinh capability mới trong thảo luận. OCR, embedding/vector index, hỏi đáp RAG và provider calls thuộc Phase 3 hoặc các phase mở rộng; ticket/incident analysis thuộc Phase 4; report/PDF thuộc Phase 5; MCP/AI Agent, tools, connector hệ thống thật và scheduler vẫn nằm ngoài MVP hiện tại.
</deferred>

---

*Phase: 2-dataset-ingestion-and-source-lifecycle*  
*Context gathered: 2026-10-07; `--auto` selected the recommended default for all four areas.*

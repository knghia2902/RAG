# Phase 1: Local Workspace and Access Control - Context

**Gathered:** 2026-10-03
**Status:** Ready for planning

<domain>
## Phase Boundary

Nền tảng Web/API/database local bằng Docker Compose, tài khoản Admin/Kỹ thuật viên, quản lý tài khoản, dataset metadata và cấp/thu hồi quyền dataset. Thiết lập cấu trúc module/contracts cho các chức năng ở phase sau. Yêu cầu sở hữu: AUTH-01–05, SYS-01, SYS-04.

Stack giữ nguyên: Python/FastAPI, LangChain, PostgreSQL/pgvector, Next.js/TypeScript; OpenAI Embeddings và LLM API qua hai provider độc lập ở phase 3. Phase 1 chưa triển khai ingestion tài liệu, RAG, phân tích ticket/sự cố hay báo cáo PDF.
</domain>

<decisions>
## Implementation Decisions

### Tài khoản và phiên đăng nhập

- **D-01:** Đăng nhập bằng username + mật khẩu. Không dùng email làm định danh đăng nhập trong MVP.
- **D-02:** Admin đầu tiên được tạo bằng lệnh khởi tạo sau khi chạy Docker Compose; nhập username/mật khẩu lúc chạy. Chạy lại không ghi đè tài khoản hiện có.
- **D-03:** Quên mật khẩu: Admin cấp mật khẩu tạm; người dùng bắt buộc đổi ở lần đăng nhập tiếp theo. Chưa có gửi email khôi phục. Luồng đổi mật khẩu phải khả dụng trước khi cho dùng chức năng nghiệp vụ.
- **D-04:** Phiên hết sau 30 phút không hoạt động, có thời hạn tuyệt đối tối đa 8 giờ. Đăng xuất hoặc vô hiệu hóa tài khoản thu hồi phiên. Cơ chế session cụ thể do researcher/planner lựa chọn; polling tự động không nên được coi là hoạt động người dùng để kéo dài idle timeout.

### Quyền theo dataset

- **D-05:** Dataset là đơn vị cấp quyền MVP, không theo từng file hoặc nhóm phòng ban. Admin cấp/thu hồi dataset cho từng Kỹ thuật viên. Admin quản trị tài khoản/tài liệu/cấu hình và xem toàn bộ báo cáo theo phạm vi đã chốt.
- **D-06:** Kỹ thuật viên mới mặc định không có quyền dataset nào. UI hiển thị hướng dẫn liên hệ Admin khi chưa được cấp quyền.
- **D-07:** Nếu báo cáo dùng dataset A và B nhưng người dùng mất quyền A, chặn toàn bộ nội dung báo cáo/PDF, thông báo quyền đã thay đổi; có thể tạo báo cáo mới chỉ từ B. Đây là policy contract cho phase báo cáo, không thêm triển khai báo cáo vào phase 1. Không để thông báo lộ nội dung/chi tiết dataset bị thu hồi.
- **D-08:** Kỹ thuật viên chỉ tra cứu/phân tích/tạo báo cáo trong dataset được cấp; Admin quản lý upload tài liệu/log, xóa và reindex. Kỹ thuật viên vẫn được nhập/upload ticket để phân tích trong phạm vi quyền ở phase 4; ngoại lệ này không cấp quyền quản lý kho tài liệu chung.
- **D-09:** Carry forward: kiểm tra quyền phía backend trên metadata, truy xuất, nguồn, kết quả/lịch sử và PDF khi các module tương ứng được thêm. Không chỉ ẩn chức năng trong UI. Quyền được kiểm tra lại theo trạng thái hiện tại.

### Giao diện quản trị

- **D-10:** Sidebar bên trái, bảng danh sách và biểu mẫu trong vùng chính. Phase 1 có Tài khoản, Dataset và Cấu hình phù hợp role; chức năng RAG/phân tích/báo cáo được bổ sung đúng phase, không tạo chức năng giả.
- **D-11:** Sau đăng nhập Admin vào Tài khoản; Kỹ thuật viên vào Dataset được cấp. Khi chưa có quyền, hiển thị hướng dẫn liên hệ Admin.
- **D-12:** Giao diện tiếng Việt; giữ thuật ngữ kỹ thuật Dataset, API, WMS/TMS khi phù hợp. Không cần bộ chuyển Việt/Anh trong phase này.
- **D-13:** Tạo tài khoản/chỉnh quyền dataset bằng panel bên phải cạnh bảng; lưu thành công cập nhật bảng. Chi tiết UI như typography, màu, kích thước, validation và responsive do bước UI/planning cụ thể hóa trong bố cục đã chốt.

### Khởi động và dữ liệu demo

- **D-14:** MVP chỉ truy cập localhost trên máy chạy Docker; mặc định không publish cho LAN. Port binding/mạng nội bộ containers phải bảo đảm phạm vi này, không chỉ ghi localhost trong hướng dẫn.
- **D-15:** Có lệnh seed riêng cho tài khoản Kỹ thuật viên và dataset metadata mẫu chưa có tài liệu; thể hiện cả trường hợp có quyền và chưa có quyền. Nhập mật khẩu khi chạy; chạy lại không ghi đè dữ liệu hoặc đổi quyền hiện có. Seed không thay thế lệnh bootstrap Admin.
- **D-16:** Không có OpenAI key vẫn khởi động và sử dụng được phần quản trị. Web hiển thị “Chưa cấu hình AI”; chức năng cần AI ở phase sau yêu cầu key và báo lỗi cấu hình rõ ràng. Phase 1 không cần gọi OpenAI để nghiệm thu.
- **D-17:** Cấu hình lần đầu qua `.env` và hướng dẫn chạy: database/secrets/OpenAI key tại máy chạy Docker. Web chỉ hiển thị trạng thái, không hiển thị giá trị secrets. Không nhập/chỉnh API key qua Web trong phase 1; cấu hình provider qua Web đầy đủ thuộc scope SYS-02 ở phase 3. `.env` thật không được đưa vào Git, chỉ `.env.example` dùng placeholder.

### Implementation Discretion

Người dùng không chọn thư viện auth/UI/queue hay session transport cụ thể; researcher/planner quyết định trong stack đã khóa và các behavior ở trên. Không diễn giải đây là quyền thay đổi thời hạn phiên, role, dataset policy hoặc scope. Username normalization, password policy, bảo vệ Admin cuối cùng và semantics cấp quyền cần được cụ thể hóa trong kế hoạch, không ghi là lựa chọn đã được người dùng trả lời.
</decisions>

<canonical_refs>
## Canonical References

Downstream researcher/planner/executor phải đọc các nguồn này. Nếu bản nghiên cứu còn ghi dataset ACL là đề xuất, D-05 trong context này là quyết định đã được người dùng chốt sau nghiên cứu.

### Scope and Contracts
- `.planning/PROJECT.md` — stack, cấu trúc thư mục và giới hạn MVP.
- `.planning/REQUIREMENTS.md` — AUTH-01–05, SYS-01, SYS-04 và contracts cho modules về sau.
- `.planning/ROADMAP.md` — phase 1 boundary, success criteria và dependencies.
- `.planning/config.json` — quy trình tự động, standard granularity, parallel independent plans, inherit models.
- `AGENTS.md` — hướng dẫn repo/GSD và trigger graphify.

### Research
- `.planning/research/STACK.md` — stack đã cập nhật, compatibility/pin gates; library phụ là đề xuất.
- `.planning/research/ARCHITECTURE.md` — boundaries, canonical data, providers, ACL và report service.
- `.planning/research/PITFALLS.md` — quyền, lifecycle, secrets và failure modes cần tránh.

Không có SPEC/ADR bên ngoài được người dùng tham chiếu trong cuộc thảo luận; quyết định phase nằm trong context này. DISCUSSION-LOG chỉ dành cho audit, không phải input lập kế hoạch.
</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- Chưa có mã nguồn ứng dụng, components, auth helpers, migrations hoặc Docker config để tái sử dụng. Repo hiện có planning/research và AGENTS.md.

### Established Patterns
- Cấu trúc được người dùng khóa: `backend/app/{api,rag,llm,database,auth}`, `backend/app/modules/{log_analysis,tickets,reports}`, `backend/tests`, `backend/scripts`, `frontend`, `data/{sample,uploads}`, `storage`, `docs`, `docker-compose.yml`.
- FastAPI routes gọi services; Next.js là Web layer; parser/provider độc lập với module nghiệp vụ. Không dùng fallback kiến trúc Qdrant/Vite của nghiên cứu ban đầu.

### Integration Points
- `backend/app/auth/`: account/session/role và policy dataset dùng chung.
- `backend/app/database/`: schema/migrations cho account, session nếu cần, dataset metadata và grants.
- `backend/app/api/`: auth/users/datasets/status contracts; các module về sau gọi cùng policy.
- `backend/scripts/`: bootstrap Admin và seed riêng, không ghi đè.
- `frontend/`: login, forced password change, role-based landing, sidebar/tables/right panels/status.
- `docker-compose.yml`, `.env.example`, `docs/`: local startup/persistence và hướng dẫn cấu hình.
</code_context>

<specifics>
## Specific Ideas

- Dataset minh họa có thể là WMS, TMS hoặc SOP nội bộ; đây là ví dụ, không giới hạn taxonomy hoặc bắt buộc tên seed.
- Thông báo “Chưa cấu hình AI” khi chưa có key; account/dataset management vẫn hoạt động.
- Nếu báo cáo A+B bị chặn do mất A, người dùng có thể tạo báo cáo mới từ B; chưa triển khai report UI trong phase 1.
</specifics>

<deferred>
## Deferred Ideas

Không phát sinh capability mới trong thảo luận. Các chức năng đã có roadmap tiếp tục thuộc phase tương ứng: ingestion/source management phase 2, RAG và provider config phase 3, ticket upload/analysis phase 4, báo cáo/PDF phase 5. OCR, scheduler, MCP, AI Agent/tools và connectors thật ngoài MVP. Email recovery, song ngữ và LAN access không được chọn cho phase 1.
</deferred>

---
*Phase: 01-local-workspace-and-access-control*
*Context gathered: 2026-10-03; user authorized creation after reviewing all four areas.*

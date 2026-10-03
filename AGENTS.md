<!-- GSD:project-start source:PROJECT.md -->

## Project

**Modular RAG cho IT & Logistics**

Ứng dụng Web RAG cho môi trường doanh nghiệp logistics, hỗ trợ kỹ thuật viên phân tích log/sự cố, xử lý ticket IT và tạo báo cáo sự cố IT kết hợp sự cố hệ thống logistics. MVP sử dụng dữ liệu mẫu, tổng hợp bằng chứng từ log, ticket, SOP và dữ liệu vận hành để đưa ra phân tích, đề xuất và nguồn trích dẫn có thể kiểm tra.

Backend được thiết kế theo API, tách RAG Core và LLM Provider để sau này kết nối MCP hoặc phát triển AI Agent. Giai đoạn MVP chỉ phân tích và đề xuất, chưa thực hiện hành động trên hệ thống thật.

Stack đã chốt: Python + FastAPI, LangChain, PostgreSQL + pgvector, OpenAI Embeddings, OpenAI API cho generation, Next.js + TypeScript và Docker Compose. Embedding Provider và LLM Provider tách riêng để thay model local hoặc Gemini sau này.

**Core Value:** Kỹ thuật viên có thể tìm bằng chứng liên quan và nhận phân tích, đề xuất xử lý sự cố logistics kèm nguồn trích dẫn để kiểm tra lại.

### Constraints

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

<!-- GSD:project-end -->

<!-- GSD:stack-start source:research/STACK.md -->

## Technology Stack

## Recommended Stack

| Thành phần | Phiên bản/baseline đã đối chiếu | Vai trò và lý do đề xuất |
|---|---|---|
| Python | 3.12.15 | Backend và worker; ecosystem xử lý tài liệu/embedding. Baseline chủ động, không tuyên bố là Python mới nhất. |
| FastAPI | 0.142.2 trên trang releases | API Web, schema request/response và OpenAPI; RAG services tách khỏi route handlers. |
| Next.js + TypeScript | Exact Next.js/React/TypeScript versions khóa khi scaffold | Frontend đã được người dùng chọn; App Router và UI gọi FastAPI, không nhân đôi business logic trong Next.js routes. |
| PostgreSQL | 18, major của tài liệu current | Nguồn chuẩn cho metadata, log events, tickets, incidents, jobs và số liệu báo cáo. |
| pgvector | 0.8.7 theo README chính thức; image tag 0.8.7-pg18 được liệt kê | Vector index trong PostgreSQL, cùng nơi lưu metadata/structured records. |
| LangChain | Exact langchain/core/integration versions khóa cùng nhau khi scaffold | Loader/chunker/retriever pipeline; dùng langchain-openai và adapter pgvector, không dùng Agent trong MVP. |
| Docling | 2.132.0 trên trang releases | Adapter xử lý PDF/DOCX; cần thử khả năng giữ vị trí nguồn trên bộ SOP mẫu. |
| OpenAI Embeddings | Model do cấu hình; baseline đề xuất text-embedding-3-small, 1536 chiều | User chọn provider API cho MVP; giữ Embedding Provider riêng để thay local và reindex sau này. |
| WeasyPrint | 70.0 theo tài liệu stable | Xuất PDF từ template HTML/CSS do ứng dụng kiểm soát; font tiếng Việt đóng gói local. |
| Celery | 5.6.3 theo tài liệu stable | Worker ingestion/report tách API; queue và job status lưu bền vững. Broker exact version chưa chốt. |

## Supporting Libraries and Tools

- Pydantic 2.x: validation DTO và output LLM; exact patch khóa cùng FastAPI.
- SQLAlchemy 2.0.54: baseline maintenance được đối chiếu; Alembic, psycopg3 và LangChain/pgvector integration cần resolve/lock cùng nhau khi triển khai.
- CSV parser và openpyxl/pandas qua adapter riêng: giữ sheet/row, kiểu dữ liệu và kiểm tra schema, không dùng text conversion để tính KPI. Exact versions chưa xác minh, không dùng như pin triển khai.
- Docker Compose đã chốt cho local services/volumes và Linux worker; worker dùng backend image với entrypoint riêng.
- Lockfiles, image tags/digests và model revision; không dùng tag `latest` trong cấu hình tái lập.
- Next.js docs nêu Node tối thiểu 20.9; chọn Node LTS còn được hỗ trợ khi scaffold và kiểm tra constraint của phiên bản pin, không dùng minimum làm cam kết compatibility toàn stack.

## Retrieval and Provider Strategy

Use PostgreSQL exact identifiers/text search and pgvector dense retrieval through LangChain. Embed with OpenAI in the MVP; generation uses only selected evidence. Embedding Provider and LLM Provider are separate. Enforce dataset ACL and active source versions before retrieval and current permissions before source/history/PDF responses. Store embedding model/dimension/index version and rebuild on model changes.

## Alternatives Considered

| Phương án | Khi phù hợp |
|---|---|
| Qdrant thay pgvector | Chỉ xem lại nếu benchmark/chức năng vượt khả năng stack đã chốt; không đưa vào Compose MVP. |
| React/Vite hoặc Vue thay Next.js | Phương án ban đầu đã bị quyết định Next.js của người dùng thay thế. |
| Worker dùng queue PostgreSQL thay Celery/broker | Quy mô nhỏ, muốn ít services; phải tự đảm bảo lease, retry, recovery và idempotency. |
| LlamaIndex thay LangChain | Không dùng trong MVP đã chốt LangChain. |
| Parser nhẹ thay Docling | PDF text đơn giản và máy yếu; phải giữ provenance và bảng đúng. |

## What NOT to Use

Do not add Qdrant, Vite, local embeddings, Agent tools, OCR, MCP or a report scheduler to the MVP in place of the user-selected stack/scope. Never derive report totals from top-k context or rely on frontend-only permissions.

## Compatibility and Installation Gate

Verify and lock FastAPI/LangChain integrations/psycopg/pgvector/Next.js dependencies at implementation time. Documentation baselines are not a tested full-stack lockfile. Keep secrets server-side and cloud tracing disabled by default.

## Sources

- [OpenAI embeddings](https://developers.openai.com/api/docs/guides/embeddings), [LangChain OpenAIEmbeddings](https://docs.langchain.com/oss/python/integrations/embeddings/openai), [LangChain pgvector](https://docs.langchain.com/oss/python/integrations/vectorstores/pgvector), [pgvector](https://github.com/pgvector/pgvector), [Next.js installation](https://nextjs.org/docs/app/getting-started/installation).
- Các nguồn Qdrant/Vite/BGE dưới đây thuộc nghiên cứu phương án ban đầu; không phải stack MVP hiện tại.
- [Python 3.12](https://docs.python.org/3.12/), [FastAPI releases](https://github.com/fastapi/fastapi/releases), [FastAPI worker guidance](https://fastapi.tiangolo.com/tutorial/background-tasks/).
- [React versions](https://react.dev/versions), [Vite requirements](https://vite.dev/guide/), [Pydantic](https://docs.pydantic.dev/latest/), [SQLAlchemy baseline](https://docs.sqlalchemy.org/en/20/).
- [PostgreSQL aggregate functions](https://www.postgresql.org/docs/current/functions-aggregate.html), [text search](https://www.postgresql.org/docs/current/textsearch-controls.html).
- [Qdrant releases](https://github.com/qdrant/qdrant/releases), [local deployment](https://qdrant.tech/documentation/quickstart/), [hybrid queries](https://qdrant.tech/documentation/search/hybrid-queries/).
- [Docling releases](https://github.com/docling-project/docling/releases), [formats](https://docling-project.github.io/docling/usage/supported_formats/).
- [BGE-M3 model card](https://huggingface.co/BAAI/bge-m3), [WeasyPrint](https://doc.courtbouillon.org/weasyprint/stable/first_steps.html), [Celery](https://docs.celeryq.dev/en/stable/getting-started/introduction.html), [Ollama API](https://docs.ollama.com/api/introduction).

<!-- GSD:stack-end -->

<!-- GSD:conventions-start source:CONVENTIONS.md -->

## Conventions

Conventions not yet established. Will populate as patterns emerge during development.
<!-- GSD:conventions-end -->

<!-- GSD:architecture-start source:ARCHITECTURE.md -->

## Architecture

This is a new project with no implementation yet. Follow the user-selected structure in `.planning/PROJECT.md` and research architecture in `.planning/research/ARCHITECTURE.md`: `backend/app/{api,rag,llm,database,auth}`, modules `{log_analysis,tickets,reports}`, `frontend`, `data/{sample,uploads}`, `storage`, `docs`, and `docker-compose.yml`. FastAPI routes call services; Next.js is the Web layer; reports use deterministic database metrics and evidence-backed narrative. Keep parser and provider adapters replaceable.
<!-- GSD:architecture-end -->

<!-- GSD:skills-start source:skills/ -->

## Project Skills

No project skills found. Add skills to any of: `.claude/skills/`, `.agents/skills/`, `.cursor/skills/`, `.github/skills/`, or `.codex/skills/` with a `SKILL.md` index file.
<!-- GSD:skills-end -->

<!-- GSD:workflow-start source:GSD defaults -->

## GSD Workflow Enforcement

Before using Edit, Write, or other file-changing tools, start work through a GSD command so planning artifacts and execution context stay in sync.

Use these entry points:

- `$gsd-quick` for small fixes, doc updates, and ad-hoc tasks
- `$gsd-debug` for investigation and bug fixing
- `$gsd-execute-phase` for planned phase work

Do not make direct repo edits outside a GSD workflow unless the user explicitly asks to bypass it.
<!-- GSD:workflow-end -->

## graphify

- **graphify** (`~/.Codex/skills/graphify/SKILL.md`) — any input to knowledge graph. Trigger: `/graphify`.
- When the user types `/graphify`, invoke the Skill tool with `skill: "graphify"` before doing anything else.

<!-- GSD:profile-start -->

## Developer Profile

> Profile not yet configured. Run `$gsd-profile-user` to generate your developer profile.
> This section is managed by `generate-claude-profile` -- do not edit manually.
<!-- GSD:profile-end -->

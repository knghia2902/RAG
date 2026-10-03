# Stack Research

**Domain:** RAG hỗ trợ sự cố IT logistics, Web MVP local.
**Researched:** 2026-10-03
**Confidence:** HIGH về khả năng thư viện; MEDIUM về lựa chọn phù hợp và hiệu năng chưa benchmark.
**Status:** Cập nhật theo stack người dùng đã chốt; các thư viện phụ là đề xuất. FastAPI + LangChain + PostgreSQL/pgvector + OpenAI Embeddings/LLM + Next.js/TypeScript + Docker Compose thay đề xuất ban đầu.

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

Baseline: exact lookup PostgreSQL cho order_id/error_code/correlation_id + lexical text search PostgreSQL + dense pgvector retrieval; hợp nhất rank trong RAG Core qua LangChain pipeline. Với tiếng Việt bắt đầu cấu hình `simple`, giữ mã kỹ thuật nguyên vẹn và đo recall; không giả định stemming tiếng Anh phù hợp.

MVP embedding và generation dùng OpenAI API, qua hai provider interface riêng. Index lưu embedding model/dimension/version. Generation chỉ gửi retrieved context; embedding cần gửi chunk index và query. Không để DTO/domain phụ thuộc SDK. Local/Gemini adapters triển khai sau.

Baseline 1536 chiều phù hợp giới hạn HNSW `vector` 2000 chiều; nếu chọn embedding lớn 3072 chiều phải giảm dimension hoặc chọn kiểu/index khác và benchmark. Với dữ liệu nhỏ bắt đầu exact nearest-neighbor, thêm HNSW sau đo. Approximate search có thể hụt kết quả khi lọc dataset; thử iterative scans/fallback, không nới quyền để bù recall.

Tài liệu PGVector integration của LangChain yêu cầu psycopg3 và ghi hạn chế migration schema. Giữ canonical sources/ACL riêng và index có thể rebuild; kiểm tra adapter/API hiện hành trước pin, không tự để thư viện sở hữu toàn bộ schema nghiệp vụ. Cloud tracing như LangSmith tắt mặc định để tránh đường egress không được yêu cầu.

## Alternatives Considered

| Phương án | Khi phù hợp |
|---|---|
| Qdrant thay pgvector | Chỉ xem lại nếu benchmark/chức năng vượt khả năng stack đã chốt; không đưa vào Compose MVP. |
| React/Vite hoặc Vue thay Next.js | Phương án ban đầu đã bị quyết định Next.js của người dùng thay thế. |
| Worker dùng queue PostgreSQL thay Celery/broker | Quy mô nhỏ, muốn ít services; phải tự đảm bảo lease, retry, recovery và idempotency. |
| LlamaIndex thay LangChain | Không dùng trong MVP đã chốt LangChain. |
| Parser nhẹ thay Docling | PDF text đơn giản và máy yếu; phải giữ provenance và bảng đúng. |

## What NOT to Use

Không dùng vector-only cho mã đơn hàng; không để LLM tự tính tổng từ top-k; không làm Agent/tool execution ở MVP; không lấy job quan trọng chạy fire-and-forget trong API. FastAPI docs gợi ý công cụ worker riêng cho xử lý nặng; độ bền queue vẫn cần thiết kế retry/idempotency.

## Compatibility and Installation Gate

Chưa cài dependency hay thử tương thích. Trước scaffold: xác minh Python/package constraints, Next.js/Node LTS, PostgreSQL/pgvector, psycopg3 và LangChain integrations; tạo lockfiles; smoke test parser, embedding và PDF trong container. OCR/PDF scan và DOC/XLS cũ ngoài MVP. Generation model cụ thể chưa chốt; không tự suy ra model mới nhất hay account availability.

## Sources

- [OpenAI embeddings](https://developers.openai.com/api/docs/guides/embeddings), [LangChain OpenAIEmbeddings](https://docs.langchain.com/oss/python/integrations/embeddings/openai), [LangChain pgvector](https://docs.langchain.com/oss/python/integrations/vectorstores/pgvector), [pgvector](https://github.com/pgvector/pgvector), [Next.js installation](https://nextjs.org/docs/app/getting-started/installation).
- Các nguồn Qdrant/Vite/BGE dưới đây thuộc nghiên cứu phương án ban đầu; không phải stack MVP hiện tại.
- [Python 3.12](https://docs.python.org/3.12/), [FastAPI releases](https://github.com/fastapi/fastapi/releases), [FastAPI worker guidance](https://fastapi.tiangolo.com/tutorial/background-tasks/).
- [React versions](https://react.dev/versions), [Vite requirements](https://vite.dev/guide/), [Pydantic](https://docs.pydantic.dev/latest/), [SQLAlchemy baseline](https://docs.sqlalchemy.org/en/20/).
- [PostgreSQL aggregate functions](https://www.postgresql.org/docs/current/functions-aggregate.html), [text search](https://www.postgresql.org/docs/current/textsearch-controls.html).
- [Qdrant releases](https://github.com/qdrant/qdrant/releases), [local deployment](https://qdrant.tech/documentation/quickstart/), [hybrid queries](https://qdrant.tech/documentation/search/hybrid-queries/).
- [Docling releases](https://github.com/docling-project/docling/releases), [formats](https://docling-project.github.io/docling/usage/supported_formats/).
- [BGE-M3 model card](https://huggingface.co/BAAI/bge-m3), [WeasyPrint](https://doc.courtbouillon.org/weasyprint/stable/first_steps.html), [Celery](https://docs.celeryq.dev/en/stable/getting-started/introduction.html), [Ollama API](https://docs.ollama.com/api/introduction).

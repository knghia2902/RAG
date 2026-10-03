# Stack Research

**Domain:** RAG hỗ trợ sự cố IT logistics, Web MVP local.
**Researched:** 2026-10-03
**Confidence:** HIGH về khả năng thư viện; MEDIUM về lựa chọn phù hợp và hiệu năng chưa benchmark.
**Status:** Đề xuất nghiên cứu, chưa phải quyết định stack đã được người dùng chốt.

## Recommended Stack

| Thành phần | Phiên bản/baseline đã đối chiếu | Vai trò và lý do đề xuất |
|---|---|---|
| Python | 3.12.15 | Backend và worker; ecosystem xử lý tài liệu/embedding. Baseline chủ động, không tuyên bố là Python mới nhất. |
| FastAPI | 0.142.2 trên trang releases | API Web, schema request/response và OpenAPI; RAG services tách khỏi route handlers. |
| React + TypeScript + Vite | React 19.3.0; Vite exact version cần khóa khi scaffold | SPA nội bộ cho dữ liệu, phân tích, hỏi đáp và báo cáo; không cần SSR cho MVP này. |
| PostgreSQL | 18, major của tài liệu current | Nguồn chuẩn cho metadata, log events, tickets, incidents, jobs và số liệu báo cáo. |
| Qdrant | 1.19.1 trên trang releases | Vector index local, metadata filters và hỗ trợ hybrid retrieval. |
| Docling | 2.132.0 trên trang releases | Adapter xử lý PDF/DOCX; cần thử khả năng giữ vị trí nguồn trên bộ SOP mẫu. |
| BAAI/bge-m3 | Model revision SHA cần khóa khi tải | Ứng viên embedding local đa ngôn ngữ; vector 1024 chiều. Chất lượng tiếng Việt/log phải đo trên dữ liệu dự án. |
| WeasyPrint | 70.0 theo tài liệu stable | Xuất PDF từ template HTML/CSS do ứng dụng kiểm soát; font tiếng Việt đóng gói local. |
| Celery | 5.6.3 theo tài liệu stable | Worker ingestion/report tách API; queue và job status lưu bền vững. Broker exact version chưa chốt. |

## Supporting Libraries and Tools

- Pydantic 2.x: validation DTO và output LLM; exact patch khóa cùng FastAPI.
- SQLAlchemy 2.0.54: baseline maintenance được đối chiếu; Alembic, psycopg và qdrant-client cần resolve/lock cùng nhau khi triển khai.
- CSV parser và openpyxl/pandas qua adapter riêng: giữ sheet/row, kiểu dữ liệu và kiểm tra schema, không dùng text conversion để tính KPI. Exact versions chưa xác minh, không dùng như pin triển khai.
- Docker Compose đề xuất cho local services/volumes và Linux worker, giúp tránh khác biệt thư viện PDF/OCR trên Windows. Đây là phương án cần chốt, chưa phải ràng buộc người dùng.
- Lockfiles, image tags/digests và model revision; không dùng tag `latest` trong cấu hình tái lập.
- Vite docs yêu cầu Node 20.19+ hoặc 22.12+; chọn Node LTS còn được hỗ trợ ở thời điểm scaffold, không suy ra toàn bộ các phiên bản tối thiểu vẫn đang được hỗ trợ.

## Retrieval and Provider Strategy

Baseline: exact lookup PostgreSQL cho order_id/error_code/correlation_id + lexical text search PostgreSQL + dense search Qdrant; hợp nhất rank trong RAG Core. Có thể chuyển lexical branch sang sparse Qdrant sau benchmark, không bắt buộc hai lexical engines trong MVP. Với tiếng Việt bắt đầu cấu hình `simple`, giữ mã kỹ thuật nguyên vẹn và đo recall; không giả định stemming tiếng Anh phù hợp.

Embedding chạy local. LLM generation dùng provider interface riêng, cấu hình endpoint/model/timeouts/context budget từ server; provider API ngoài cụ thể chưa chọn. Ollama là ứng viên adapter local sau này. Không để DTO/domain phụ thuộc SDK một nhà cung cấp.

## Alternatives Considered

| Phương án | Khi phù hợp |
|---|---|
| PostgreSQL + pgvector thay Qdrant | Muốn ít services hơn; cần benchmark vector filtering/hybrid trước quyết định. |
| Vue thay React | Có ưu tiên hoặc đội ngũ đã có chuẩn Vue; nghiệp vụ không phụ thuộc framework UI. |
| Worker dùng queue PostgreSQL thay Celery/broker | Quy mô nhỏ, muốn ít services; phải tự đảm bảo lease, retry, recovery và idempotency. |
| LangChain/LlamaIndex | Dùng adapter khi có lợi; chưa cần đưa framework orchestration vào domain core. |
| Parser nhẹ thay Docling | PDF text đơn giản và máy yếu; phải giữ provenance và bảng đúng. |

## What NOT to Use

Không dùng vector-only cho mã đơn hàng; không để LLM tự tính tổng từ top-k; không làm Agent/tool execution ở MVP; không lấy job quan trọng chạy fire-and-forget trong API. FastAPI docs gợi ý công cụ worker riêng cho xử lý nặng; độ bền queue vẫn cần thiết kế retry/idempotency.

## Compatibility and Installation Gate

Chưa cài dependency hay thử tương thích. Trước scaffold: xác minh Python/package constraints, Node LTS, client/server Qdrant; tạo lockfiles; smoke test parser, embedding và PDF trong container. Benchmark RAM/CPU trên máy đích trước chốt BGE-M3. OCR/PDF scan và DOC/XLS cũ cần scope riêng; hỗ trợ format của thư viện không đồng nghĩa MVP đã hỗ trợ.

## Sources

- [Python 3.12](https://docs.python.org/3.12/), [FastAPI releases](https://github.com/fastapi/fastapi/releases), [FastAPI worker guidance](https://fastapi.tiangolo.com/tutorial/background-tasks/).
- [React versions](https://react.dev/versions), [Vite requirements](https://vite.dev/guide/), [Pydantic](https://docs.pydantic.dev/latest/), [SQLAlchemy baseline](https://docs.sqlalchemy.org/en/20/).
- [PostgreSQL aggregate functions](https://www.postgresql.org/docs/current/functions-aggregate.html), [text search](https://www.postgresql.org/docs/current/textsearch-controls.html).
- [Qdrant releases](https://github.com/qdrant/qdrant/releases), [local deployment](https://qdrant.tech/documentation/quickstart/), [hybrid queries](https://qdrant.tech/documentation/search/hybrid-queries/).
- [Docling releases](https://github.com/docling-project/docling/releases), [formats](https://docling-project.github.io/docling/usage/supported_formats/).
- [BGE-M3 model card](https://huggingface.co/BAAI/bge-m3), [WeasyPrint](https://doc.courtbouillon.org/weasyprint/stable/first_steps.html), [Celery](https://docs.celeryq.dev/en/stable/getting-started/introduction.html), [Ollama API](https://docs.ollama.com/api/introduction).

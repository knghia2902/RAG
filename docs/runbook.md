# Cẩm nang Vận hành Hệ thống Modular RAG cho IT & Logistics (Operations Runbook)

Tài liệu hướng dẫn triển khai, vận hành hàng ngày, khắc phục sự cố và nghiệm thu kỹ thuật cho hệ thống **Modular RAG IT & Logistics** trên môi trường Local Docker Compose.

---

## 1. Kiến trúc triển khai Local Docker Compose

Hệ thống được thiết kế theo kiến trúc microservices tách biệt giữa Web UI, API Backend, Queue Worker, CSDL quan hệ kết hợp Vector Store, và Message Broker:

```mermaid
flowchart TD
    User([Người dùng / Kỹ thuật viên]) -->|HTTP :3000| WebUI[Frontend: Next.js + React]
    WebUI -->|REST API :8000| Backend[API Gateway: FastAPI]
    Backend -->|SQLAlchemy & pgvector| Postgres[(PostgreSQL 18 + pgvector 0.8.7)]
    Backend -->|Push Task| RabbitMQ((RabbitMQ 4 Message Broker))
    RabbitMQ -->|Consume Task| CeleryWorker[Worker: Celery Ingestion & Export]
    CeleryWorker -->|Read/Write Vectors| Postgres
```

### Danh mục Containers và Cổng mạng

| Tên Container | Hình ảnh / Phiên bản | Cổng Host | Vai trò |
|---|---|---|---|
| `postgres` | `pgvector/pgvector:0.8.7-pg18` | `5432:5432` | Lưu trữ metadata, tài khoản, log, ticket, incident, reports và 1536-dim vector embeddings. |
| `rabbitmq` | `rabbitmq:4-management` | `5672:5672`, `15672:15672` | Broker điều phối hàng đợi xử lý tệp nạp nguồn và báo cáo nền. |
| `migrate` | `logistics-rag-backend:phase1` | — | Khởi chạy Alembic migration đồng bộ schema CSDL khi khởi động. |
| `backend` | `logistics-rag-backend:phase1` | `8000:8000` | REST API FastAPI, RAG Hybrid Retrieval, Live Scope Recheck, Incident Analysis. |
| `worker` | `logistics-rag-backend:phase1` | — | Celery worker (concurrency = 2) xử lý bóc tách tệp, băm nội dung, embed và xuất báo cáo. |
| `frontend` | `logistics-rag-web:phase1` | `3000:3000` | Giao diện Next.js App Router tiếng Việt (Datasets, Chat, Incidents, Reports). |
| `postgres-test` | `pgvector/pgvector:0.8.7-pg18` | — | CSDL độc lập cách ly cho test tự động (`rag_test`). |

---

## 2. Hướng dẫn cài đặt & Khởi động nhanh

### Yêu cầu tiên quyết
- Docker Engine $\ge 24.0$ và Docker Compose v2.
- RAM tối thiểu: 4GB (Khuyến nghị 8GB).
- Ổ đĩa trống: tối thiểu 10GB.

### Cấu hình Biến môi trường (`.env`)
Tạo hoặc kiểm tra tệp `.env` tại thư mục gốc của dự án:

```bash
# Cấu hình Database
POSTGRES_PASSWORD=your-secure-postgres-password
DATABASE_URL=postgresql+psycopg://rag:your-secure-postgres-password@postgres:5432/rag

# Cấu hình Secret & Session
SECRET_KEY=generate-a-strong-random-secret-key-32-chars
APP_ORIGIN=http://localhost:3000

# Cấu hình AI Provider (OpenAI trong MVP)
OPENAI_API_KEY=sk-your-openai-api-key-here
LANGCHAIN_TRACING_V2=false

# Cấu hình RabbitMQ
RABBITMQ_PASSWORD=rabbitmq-local-pass
CELERY_BROKER_URL=amqp://rag:rabbitmq-local-pass@rabbitmq:5672//
```

### Lệnh khởi động toàn bộ hệ thống
```bash
# Khởi động ở chế độ background
docker compose up -d

# Kiểm tra trạng thái sức khỏe các containers
docker compose ps
```

Sau khoảng 20-30 giây, tất cả các container sẽ chuyển sang trạng thái `healthy` hoặc `running`. Kiểm tra backend sẵn sàng qua endpoint:
```bash
curl http://localhost:8000/health/ready
# Phản hồi: {"status":"ready","database":"connected","version":"0.1.0"}
```

---

## 3. Khởi tạo dữ liệu Demo 1 lệnh (One-Click Demo)

Hệ thống cung cấp script tích hợp `demo_walkthrough.py` tự động khởi tạo người dùng, nạp dữ liệu mẫu logistics, phân quyền, phân tích sự cố đơn hàng `DH001` và tạo báo cáo tuần:

```bash
docker compose exec backend python scripts/demo_walkthrough.py
```

### Thông tin đăng nhập mặc định sau khi nạp demo

| Vai trò | Tên đăng nhập | Mật khẩu mặc định | Quyền hạn |
|---|---|---|---|
| **Kỹ thuật viên** | `tech` | `Tech@123456` | Xem và phân tích sự cố đơn hàng, tra cứu hỏi đáp, xem và tải báo cáo PDF trong phạm vi dataset được cấp. |
| **Quản trị viên** | `admin` | `Admin@123456` | Toàn quyền quản lý dataset, nạp tệp nguồn, cấp/thu hồi quyền kỹ thuật viên, xem toàn bộ báo cáo. |

### Các bước trải nghiệm nhanh trên trình duyệt
1. Mở trình duyệt tại địa chỉ: `http://localhost:3000/login`.
2. Đăng nhập bằng tài khoản `tech` / `Tech@123456`.
3. Mở tab **Sự cố** (`/incidents`): Xem biểu đồ phân tích sự cố đơn hàng `DH001`, timeline đối soát 3 hệ thống (WMS, API Gateway, TMS) và hướng dẫn xử lý theo SOP.
4. Mở tab **Báo cáo** (`/reports`): Xem số liệu KPI tổng hợp tuần và bấm nút **"Tải báo cáo PDF"** để xuất file PDF in ấn chuẩn tiếng Việt.

---

## 4. Vận hành & Giám sát hàng ngày

### Theo dõi nhật ký hoạt động (Logs)
```bash
# Theo dõi log backend API
docker compose logs -f backend

# Theo dõi log worker xử lý hàng đợi
docker compose logs -f worker

# Theo dõi log truy cập web frontend
docker compose logs -f frontend
```

### Chạy kiểm thử tự động toàn diện
```bash
# Chạy toàn bộ 220+ bài kiểm thử đơn vị, tích hợp và nghiệm thu
docker compose run --rm -v "${PWD}/backend:/app/backend" --no-deps backend-test pytest

# Chạy riêng suite nghiệm thu bảo mật và ground truth
docker compose run --rm -v "${PWD}/backend:/app/backend" --no-deps backend-test pytest tests/acceptance/ -v
```

### Đo lường độ trễ thực tế các khâu
```bash
# Đo lường độ trễ trên môi trường local (mặc định 5 lần lặp)
docker compose exec backend python scripts/benchmark_latency.py --iterations 5
```

---

## 5. Quy trình xử lý sự cố (Troubleshooting & Disaster Recovery)

### Sự cố 1: Worker Celery bị treo hoặc crash khi đang xử lý tệp
- **Hiện tượng:** Tệp nạp vào ở trạng thái `processing` kéo dài, không chuyển sang `ready`.
- **Nguyên nhân:** Container worker bị khởi động lại đột ngột hoặc mất kết nối broker.
- **Cách xử lý:**
  1. Cơ chế Lease Idempotency tự động giải phóng bản ghi sau khi hết hạn `lease_expires_at` (10 phút).
  2. Khởi động lại worker:
     ```bash
     docker compose restart worker
     ```
  3. Quản trị viên vào giao diện `/datasets/{id}` bấm nút **"Thử lại" (Retry)** trên tệp lỗi để đưa job trở lại hàng đợi `queued`.

### Sự cố 2: Lỗi kết nối CSDL hoặc Migration chưa áp dụng
- **Hiện tượng:** Backend trả về mã HTTP 503 "Dịch vụ tạm thời không khả dụng".
- **Cách xử lý:**
  ```bash
  # Kiểm tra trạng thái Alembic
  docker compose run --rm backend-test python -m alembic current
  
  # Cập nhật migration lên bản mới nhất
  docker compose run --rm backend-test python -m alembic upgrade head
  ```

---

## 6. Quy trình Tái lập chỉ mục Vector không Downtime (Zero-Downtime Reindexing)

Khi nâng cấp mô hình Embedding (ví dụ: chuyển từ `text-embedding-3-small` sang mô hình local mới hoặc phiên bản vector mới), hệ thống áp dụng cơ chế **Immutable Index Versioning** để đảm bảo không gián đoạn truy vấn:

1. **Giữ nguyên version hiện hành:** Bảng `embedding_records` tiếp tục phục vụ người dùng qua `index_version` cũ.
2. **Khởi tạo Version mới:**
   ```python
   new_version = uuid4()
   ```
3. **Chạy Reindex nền:** Worker tính toán embedding cho toàn bộ `CanonicalRecord` hiện có với `new_version` và lưu vào bảng `embedding_records`.
4. **Chuyển đổi Pointer hệ thống:** Cập nhật cấu hình hệ thống trỏ sang `new_version`. Toàn bộ các truy vấn tìm kiếm RAG mới sẽ ngay lập tức sử dụng index mới.
5. **Dọn dẹp vector cũ:** Xóa các bản ghi embedding thuộc version cũ sau khi đã đối soát ổn định:
   ```sql
   DELETE FROM embedding_records WHERE index_version = 'old-index-version-uuid';
   ```

---

## 7. Bảng công bố Giới hạn Vận hành Thực tế (Operational Limits)

Các giới hạn đã được kiểm chứng bằng test tự động và đo lường trên môi trường Docker Compose chuẩn:

| Thông số / Thành phần | Ngưỡng giới hạn | Hành vi xử lý khi vượt ngưỡng | Mã kiểm chứng |
|---|---|---|---|
| **Dung lượng tệp Ticket** | 5 MB | Từ chối ngay lập tức, trả mã lỗi HTTP 400 rõ ràng | `test_upload_file_size_limit_enforced` |
| **Dung lượng tệp Nguồn Nạp** | 50 MB (10 tệp/batch) | Chặn upload tại API, không lưu đĩa và không đưa vào queue | `test_source_upload_limits` |
| **Timeout gọi LLM / AI** | 30.0 giây | Ngắt kết nối an toàn, trả về `LLMTimeoutError` theo SYS-05 | `test_network_timeout_handling_sys05` |
| **Mức tải Celery đồng thời** | Concurrency = 2 | Hàng đợi RabbitMQ điều phối tuần tự, không tràn RAM | `celery_worker --concurrency=2` |
| **Độ trễ Ingestion (p50 / p95)** | **0.71 ms / 3.35 ms** | Bóc tách text log và gắn locator 1-indexed siêu tốc | `benchmark_latency.py` |
| **Độ trễ Retrieval (p50 / p95)** | **4.36 ms / 6.77 ms** | Hybrid query kết hợp pgvector cosine và lọc metadata | `benchmark_latency.py` |
| **Độ trễ Render PDF (p50 / p95)**| **430.56 ms / 854.53 ms** | WeasyPrint 70.0 biên dịch HTML/CSS sang PDF tiếng Việt | `benchmark_latency.py` |

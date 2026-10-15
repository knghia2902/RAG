---
quick: 261015-c2y
name: switch-llm-to-google-gemini
status: complete
completed_at: "2026-10-15T08:59:00+07:00"
commits:
  - 9b39fc7: feat(quick-261015-c2y): configure Gemini LLM provider, Docker network egress, and secret masking
  - 5bb26f6: feat(quick-261015-c2y): build containers and verify live Gemini RAG chat and incident reasoning
requirements:
  - ASVS-L1-SYS-02
  - ASVS-L1-SYS-03
  - ASVS-L1-SYS-05
  - RAG-01
  - RAG-04
  - RAG-05
---

# Quick Task Summary: Switch LLM Provider to Google Gemini (gemini-flash-lite-latest)

## Executive Summary

Hệ thống Logistics RAG đã hoàn thành việc tích hợp Google Gemini (`gemini-flash-lite-latest`) làm LLM Provider chính thức thông qua OpenAI-compatible endpoint (`https://generativelanguage.googleapis.com/v1beta/openai/`), sử dụng khóa `GEMINI_API_KEY` được cấu hình từ file `.env`. Trong khi đó, vector embeddings vẫn được giữ nguyên độc lập trên mô hình `text-embedding-3-small`.

Toàn bộ quá trình egress ra ngoài Internet đã được cấu hình an toàn trên Docker network bridge (`web`), bảo đảm các dịch vụ cơ sở dữ liệu (`postgres`, `postgres-test`) và hàng đợi tin nhắn (`rabbitmq`) duy trì chế độ cách ly mạng nội bộ (`internal: true`).

## Key Changes Implemented

1. **Docker Network & Container Egress (`docker-compose.yml`)**:
   - Gán `networks: [local, web]` cho cả hai dịch vụ `backend` và `worker`, cho phép DNS resolution và outbound HTTPS gọi API Google Gemini.
   - Thêm `GEMINI_API_KEY: ${GEMINI_API_KEY:-}` và `LLM_PROVIDER: ${LLM_PROVIDER:-gemini}` vào operational environment block.
   - Thiết lập `GEMINI_API_KEY: ""` và `LLM_PROVIDER: "fake"` trong test environment (`x-test-env`).
   - Duy trì `postgres`, `postgres-test`, và `rabbitmq` hoàn toàn trong isolated internal networks.

2. **Configuration & Settings (`backend/app/config.py`)**:
   - Thêm `gemini_api_key: SecretStr = SecretStr("")` và `llm_provider: str = "gemini"` vào `Settings`.

3. **OpenAI & Gemini Provider Adapters (`backend/app/providers/`)**:
   - Mở rộng `OpenAILLMAdapter` với tùy chọn `base_url: str | None = None`.
   - Tạo mới `GeminiLLMAdapter` kế thừa `OpenAILLMAdapter`, mặc định trỏ tới `gemini-flash-lite-latest` và `https://generativelanguage.googleapis.com/v1beta/openai/` với timeout 30.0s và max_tokens 2048.
   - Cập nhật `get_llm_provider()` để ưu tiên `GeminiLLMAdapter` khi có `gemini_api_key` hoặc `llm_provider == "gemini"`, giữ nguyên `FakeLLMAdapter` trong test mode và `OpenAILLMAdapter` khi cấu hình `OPENAI_API_KEY`.

4. **Status & Model Config Endpoints (`backend/app/api/`)**:
   - `/api/v1/status`: Cập nhật `provider_configured` trả về `true` khi có `openai_api_key` hoặc `gemini_api_key`.
   - `/api/v1/config/models`: Trả về `llm_provider="gemini"` và `llm_model="gemini-flash-lite-latest"` khi cấu hình Gemini, kèm cờ `gemini_configured`.

5. **Secret Masking & ASVS L1 Egress Redaction (`backend/app/llm/secret_masking.py`)**:
   - Bổ sung regex nhận diện và che giấu toàn diện Gemini API keys:
     - `\bAQ\.[a-zA-Z0-9_\-]{40,}\b` -> `[REDACTED_GEMINI_KEY]`
     - `\bAIza[0-9A-Za-z-_]{35}\b` -> `[REDACTED_GEMINI_KEY]`
   - Bảo đảm tuyệt đối không rò rỉ credential ra log hệ thống, response body, hay lỗi ngoại lệ (ASVS-L1-SYS-03).

6. **End-to-End Live Verification Script (`backend/scripts/verify_gemini_rag.py`)**:
   - Xác thực 4 bước trực tiếp trên container runtime với API Google Gemini thật:
     - Step 1: Direct Provider Generation kèm trích dẫn số thứ tự bằng chứng `[1]`, `[2]`.
     - Step 2: GroundedGenerator Pipeline trả lời tiếng Việt có trích dẫn `SourceLocator` và đánh giá cờ bất định / mâu thuẫn (RAG-01, RAG-04, RAG-05).
     - Step 3: Structured Incident Reasoning phân tích sự cố đơn hàng `DH001`, phân loại lỗi WMS-TMS, giả thuyết nguyên nhân gốc và hành động SOP.
     - Step 4: Secret Redaction & Leakage Prevention xác nhận key không rò rỉ.

## Verification & Test Results

### 1. Targeted Unit & Integration Tests
```
tests/unit/test_providers.py
tests/unit/test_secret_masking.py
tests/unit/test_module_boundaries.py
tests/integration/test_startup.py
--> 28 passed, 1 warning in 16.08s
```

### 2. Live Gemini Verification (`verify_gemini_rag.py`)
```
STARTING GOOGLE GEMINI (gemini-flash-lite-latest) END-TO-END VERIFICATION
[INFO] GEMINI_API_KEY detected: [REDACTED_GEMINI_KEY]
[INFO] Configured LLM_PROVIDER: gemini
[INFO] Test mode: False

--- STEP 1: Direct Provider Generation ---
[SUCCESS] Step 1 generated response in 0.94s
Parsed citations: 1 locators

--- STEP 2: GroundedGenerator Pipeline ---
[SUCCESS] Step 2 generated grounded answer in 1.54s
Citations count: 1 | Uncertainty flag: False | Conflict flag: False

--- STEP 3: Structured Incident Reasoning ---
[SUCCESS] Step 3 analyzed incident in 1.53s
Summary: Phân tích sự cố đơn hàng DH001: Ghi nhận 2 sự kiện log trên 2 hệ thống (WMS, API_GATEWAY). Nhóm lỗi 'Mất đồng bộ WMS-TMS do timeout kết nối', mức ưu tiên đề xuất P1.
Confidence: 0.95 | Hypotheses: 2 | Actions: 2

--- STEP 4: Secret Redaction & Leakage Prevention ---
Masked log string: Debug auth: GEMINI_API_KEY=[REDACTED_GEMINI_KEY] connecting to ...

ALL 4 VERIFICATION STEPS PASSED SUCCESSFULLY WITH GOOGLE GEMINI!
Latencies: Direct=0.94s, GroundedRAG=1.54s, IncidentReasoning=1.53s
```

### 3. Full Regression Test Suite
```
docker compose run --rm backend-test
--> 225 passed, 7 warnings in 78.85s (100% passing rate)
```

## Security Compliance (Threat Model & ASVS L1)

- **TM-SEC-01 (Information Disclosure)**: `GEMINI_API_KEY` được lưu trong `SecretStr`, chỉ hiển thị boolean flag qua status/config endpoints, và được `mask_secrets` thanh lọc thành `[REDACTED_GEMINI_KEY]`.
- **TM-SEC-02 (Network Exposure)**: Chỉ `backend` và `worker` có bridge `web`; PostgreSQL và RabbitMQ vẫn nằm trong isolated local network không có egress ra ngoài.
- **TM-SEC-03 (DoS / API Timeout)**: Cấu hình `timeout=30.0s` chặn đứng rủi ro hanging API calls, chuyển đổi thành `TimeoutError` theo SYS-05.
- **TM-SEC-04 (Grounding Integrity)**: `GroundedGenerator` và `IncidentReasoner` duy trì cơ chế thẩm định trích dẫn nguồn gốc và phân biệt rõ giả thuyết chưa xác nhận vs nguyên nhân đã xác nhận.

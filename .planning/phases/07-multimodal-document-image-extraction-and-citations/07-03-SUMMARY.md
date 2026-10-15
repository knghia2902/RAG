---
phase: 07-multimodal-document-image-extraction-and-citations
plan: "03"
subsystem: backend-multimodal-rag-gemini
tags: [multimodal, gemini, vision, rag, retrieval, prompt-construction, citations]
requires: ["07-01", "07-02"]
provides:
  - RAG retrieval association with extracted images in backend/app/rag/retrieval.py and backend/app/database/retrieval.py
  - Gemini Multimodal Vision Prompt Construction with inline base64 images in backend/app/providers/openai_llm.py
  - Bounded 3-image safety limit protecting latency and token budget (T-07-04, D-03)
  - Chat API image citations integration and preview metadata in backend/app/api/chat.py
  - Unit test suite for multimodal vision and image citations in backend/tests/unit/test_gemini_multimodal.py (7/7 passed)
affects: [07-04]
tech-stack:
  added: [Google Gemini Multimodal Vision, inline base64 parts, Markdown image citations]
  patterns: [multimodal-grounding, bounded-image-limit, image-enriched-chunks, dual-citation-metadata]
key-files:
  created:
    - backend/tests/unit/test_gemini_multimodal.py
  modified:
    - backend/app/rag/contracts.py
    - backend/app/rag/retrieval.py
    - backend/app/database/retrieval.py
    - backend/app/llm/contracts.py
    - backend/app/llm/generation.py
    - backend/app/providers/openai_llm.py
    - backend/app/providers/fake.py
    - backend/app/api/schemas.py
    - backend/app/api/chat.py
    - backend/tests/integration/test_vector_storage_migration.py
key-decisions:
  - "Mở rộng EvidenceChunk và GenerationRequest để mang metadata hình ảnh trích xuất qua các tầng RAG và LLM một cách nguyên tử."
  - "Làm giàu chunks trong execute_hybrid_retrieval và enrich_chunks_with_images với bộ lọc dataset_id nghiêm ngặt nhằm triệt tiêu rò rỉ chéo tenant (T-07-05)."
  - "Thiết lập giới hạn cứng tối đa 3 ảnh/request (prepare_multimodal_images) khi gửi tới Gemini để kiểm soát độ trễ và ngân sách context window (T-07-04, D-03)."
  - "Tích hợp hướng dẫn Markdown image citation vào system prompt và danh sách ảnh đính kèm kèm URL bảo mật vào user prompt để Gemini sinh trích dẫn ảnh chính xác (D-04)."
  - "Cập nhật endpoint Chat và Citation Preview để truyền thông tin image_id và image_url cho giao diện người dùng (D-05)."
requirements-completed: [RETR-03]
actuals:
  tasks: 3
  commits: 3
  duration: 15min
  completed: 2026-10-15
  status: complete
---

# Phase 07 Plan 03: Multimodal RAG Retrieval & Gemini Vision Generation Summary

**Triển khai hoàn chỉnh tầng suy luận đa phương thức (Multimodal Grounding & Vision Generation) với Google Gemini (`gemini-flash-lite-latest`), liên kết tự động bằng chứng văn bản với hình ảnh trích xuất của tài liệu, đóng gói payload inline base64 an toàn có giới hạn tối đa 3 ảnh, và trả về trích dẫn ảnh bảo mật trong Chat API.**

---

## Các nhiệm vụ đã hoàn thành

### 1. RAG Retrieval Association with Extracted Images (Task 07-03-01)
- Cập nhật [backend/app/rag/contracts.py](file:///D:/KhacNghia/RAG/backend/app/rag/contracts.py):
  - Bổ sung trường `images: tuple[dict, ...] = Field(default=())` cho model `EvidenceChunk`.
- Mở rộng [backend/app/rag/retrieval.py](file:///D:/KhacNghia/RAG/backend/app/rag/retrieval.py):
  - Hàm `enrich_chunks_with_images(chunks, db, image_lookup_fn, max_images_per_chunk=2, max_total_images=3)`:
    - Trích xuất `source_version_id`, `source_id`, `dataset_id`, và `page` từ từng chunk.
    - Truy vấn bảng `ExtractedImage` đảm bảo điều kiện khớp `dataset_id` (chặn rò rỉ chéo dataset - T-07-05).
    - Khớp chính xác trang (`page_number == page`) hoặc ảnh đại diện của phiên bản nếu là tài liệu một trang/DOCX.
    - Đính kèm metadata ảnh (`image_id`, `storage_path`, `mime_type`, `caption`, `page_number`, `api_url`).
  - Hàm `extract_representative_images(chunks, max_images=3)`:
    - Thu thập tối đa 2-3 ảnh tiêu biểu từ các chunks có độ tương đồng cao nhất xếp trước.
  - Hàm `retrieve_grounded_chunks`: Điều phối làm giàu và trích xuất top ảnh đại diện.
- Cập nhật [backend/app/database/retrieval.py](file:///D:/KhacNghia/RAG/backend/app/database/retrieval.py):
  - Tích hợp `enrich_chunks_with_images` trực tiếp vào bước cuối của `execute_hybrid_retrieval`, giúp các chunk trả về luôn có sẵn metadata hình ảnh.
- **Commit:** `feat(phase-07-03): associate retrieved chunks with extracted images` (`fcc6231`).

### 2. Gemini Multimodal Vision Prompt Construction (Task 07-03-02)
- Cập nhật [backend/app/llm/contracts.py](file:///D:/KhacNghia/RAG/backend/app/llm/contracts.py):
  - Bổ sung trường `images: tuple[dict, ...] = Field(default=())` vào `GenerationRequest`.
- Mở rộng [backend/app/providers/openai_llm.py](file:///D:/KhacNghia/RAG/backend/app/providers/openai_llm.py):
  - Hàm `prepare_multimodal_images`:
    - Đọc ảnh từ đường dẫn `storage_path` trên đĩa (nếu chưa có `b64`), mã hóa base64 chuẩn UTF-8.
    - Thực thi giới hạn cứng tối đa 3 ảnh/request để bảo vệ latency và token (T-07-04, D-03).
  - Hàm `build_multimodal_messages`:
    - Nếu có ảnh: tạo `user_content` dạng danh sách các phần tử theo chuẩn OpenAI/Gemini Multimodal:
      - `{"type": "text", "text": prompt_text}`
      - `{"type": "image_url", "image_url": {"url": "data:{mime_type};base64,{b64}"}}`
    - Bổ sung chỉ thị cho System Prompt:
      `"Nếu trong ngữ cảnh có hình ảnh hoặc sơ đồ kỹ thuật, hãy quan sát kỹ các thông số/chi tiết trong hình ảnh để trả lời chính xác và chèn trích dẫn ảnh bằng cú pháp Markdown: ![Mô tả ảnh](IMAGE_API_URL)."`
    - Thêm danh sách hình ảnh kèm URL API bảo mật vào ngữ cảnh prompt để Gemini đối chiếu và trích dẫn chuẩn xác.
  - Phương thức `generate` & `generate_grounded_answer`:
    - Tự động trích xuất ảnh từ `request.images` hoặc từ các `chunk.images` và gửi payload tới Gemini.
- Cập nhật [backend/app/llm/generation.py](file:///D:/KhacNghia/RAG/backend/app/llm/generation.py):
  - `GroundedGenerator.generate_answer` nhận tham số `images` và bảo toàn `images` khi cắt tỉa bằng chứng.
- Cập nhật [backend/app/providers/fake.py](file:///D:/KhacNghia/RAG/backend/app/providers/fake.py):
  - `FakeLLMAdapter` bổ sung trích dẫn hình ảnh giả lập phục vụ kiểm thử.
- **Commit:** `feat(phase-07-03): add Gemini multimodal vision prompt builder with inline base64 images` (`ba47398`).

### 3. Chat API Image Citation Integration & Tests (Task 07-03-03)
- Cập nhật [backend/app/api/schemas.py](file:///D:/KhacNghia/RAG/backend/app/api/schemas.py):
  - Bổ sung `image_id: UUID | None = None` và `image_url: str | None = None` vào `CitationPreviewResponseDTO`.
- Cập nhật [backend/app/api/chat.py](file:///D:/KhacNghia/RAG/backend/app/api/chat.py):
  - Trong `execute_query`:
    - Lấy danh sách `relevant_images = extract_representative_images(evidence_chunks, max_images=3)`.
    - Truyền `images=relevant_images` vào `generator.generate_answer`.
    - Lưu metadata trích dẫn ảnh (`image_id`, `image_url`, `caption`) vào mảng `citations` của `ChatMessage`.
  - Trong `preview_citation`:
    - Truy vấn `ExtractedImage` theo `loc_data["image_id"]` hoặc `source.active_version_id` + `page`.
    - Trả về `image_id` và `image_url` qua endpoint `/api/v1/chat/citations/preview`.
- Xây dựng bộ kiểm thử đơn vị [backend/tests/unit/test_gemini_multimodal.py](file:///D:/KhacNghia/RAG/backend/tests/unit/test_gemini_multimodal.py):
  1. `test_prepare_multimodal_images_base64_conversion`: Chuyển đổi tệp vật lý và dữ liệu ảnh sang base64 payload.
  2. `test_multimodal_image_limit_enforced_to_max_3`: Kiểm tra giới hạn cứng tối đa 3 ảnh.
  3. `test_build_multimodal_messages_structure`: Kiểm tra cấu trúc payload multimodal và inline image parts.
  4. `test_build_multimodal_messages_without_images_fallback`: Fallback về text khi không có ảnh.
  5. `test_gemini_generate_passes_multimodal_payload`: Kiểm tra GeminiLLMAdapter gửi đúng payload tới API.
  6. `test_citation_verifier_preserves_markdown_image_links`: Kiểm tra CitationVerifier bảo toàn cú pháp Markdown image.
  7. `test_enrich_chunks_with_images_and_representative_selection`: Kiểm tra làm giàu chunk và chọn ảnh tiêu biểu.
- **Commit:** `feat(phase-07-03): integrate image citations into chat API and add unit tests` (`2d22816`).

---

## Kết quả kiểm thử

Lệnh thực thi kiểm thử:
```bash
docker compose run --rm -v "${PWD}/backend:/app/backend" --no-deps backend-test pytest tests/unit/test_gemini_multimodal.py -v
```
Kết quả:
```
tests/unit/test_gemini_multimodal.py::test_prepare_multimodal_images_base64_conversion PASSED [ 14%]
tests/unit/test_multimodal_image_limit_enforced_to_max_3 PASSED          [ 28%]
tests/unit/test_gemini_multimodal.py::test_build_multimodal_messages_structure PASSED [ 42%]
tests/unit/test_gemini_multimodal.py::test_build_multimodal_messages_without_images_fallback PASSED [ 57%]
tests/unit/test_gemini_multimodal.py::test_gemini_generate_passes_multimodal_payload PASSED [ 71%]
tests/unit/test_gemini_multimodal.py::test_citation_verifier_preserves_markdown_image_links PASSED [ 85%]
tests/unit/test_gemini_multimodal.py::test_enrich_chunks_with_images_and_representative_selection PASSED [100%]

======================== 7 passed, 1 warning in 0.44s ==========================
```

Kiểm tra toàn bộ test suite liên quan đến Phase 7:
```bash
docker compose run --rm -v "${PWD}/backend:/app/backend" --no-deps backend-test pytest tests/unit/test_module_boundaries.py tests/unit/test_image_extractor.py tests/integration/test_image_api_security.py -v
======================== 26 passed, 1 warning in 11.23s ========================
```

---

## Trạng thái và bước tiếp theo

Plan 07-03 đã hoàn thành toàn bộ yêu cầu, sẵn sàng chuyển tiếp sang **Plan 07-04: Frontend Citation Previews, Lightbox Pan/Zoom & Dual UI Display**.

---
phase: 07-multimodal-document-image-extraction-and-citations
verified: 2026-10-15T10:56:00+07:00
status: passed
score: 12/12 must-haves verified
---

# Báo Cáo Nghiệm Thu Toàn Diện: Phase 07 — Multimodal Document Image Extraction and Citations

> **Mục tiêu Phase 07:** Trích xuất hình ảnh tài liệu (PDF/DOCX/datasheets, sơ đồ mạng, bảng biểu hình ảnh), lưu trữ bảo mật cục bộ, hỗ trợ RAG đa phương thức và hiển thị hình ảnh kèm trích dẫn dòng/trang trong câu trả lời AI và giao diện xem bằng chứng.
> **Requirements bao phủ:** DATA-02, DATA-03, RETR-03 (mở rộng Multimodal).
> **Trạng thái:** ✅ **PASSED (12/12 Must-Haves Verified)**

---

## 1. Tổng Quan Kết Quả Nghiệm Thu

Phase 07 đã được triển khai và kiểm chứng đầy đủ trên cả 4 plans theo đúng các quyết định thiết kế kiến trúc (D-01 đến D-11), ASVS L1 threat model mitigations (T-07-01 đến T-07-06), các hợp đồng UI/UX (`07-UI-SPEC.md`), và chiến lược kiểm thử (`07-VALIDATION.md`).

| Hạng mục kiểm tra | Tiêu chuẩn đánh giá | Kết quả thực tế | Trạng thái |
|---|---|---|---|
| **Backend Test Suite** | 244 test cases (pytest) | **244 passed**, 7 warnings trong 93.52s | ✅ PASSED |
| **Frontend Turbopack Build** | Next.js 16.3.8 compilation | **Compiled successfully in 446ms**, 11/11 static routes tối ưu | ✅ PASSED |
| **Clean Architecture & Boundary** | Không vi phạm ranh giới module | `test_module_boundaries.py` 14/14 tests passed | ✅ PASSED |
| **Live Scope Recheck & ACL** | Thu hồi quyền dataset chặn tức thời | `test_image_api_security.py` 7/7 tests passed | ✅ PASSED |
| **Multimodal Vision & Citations** | Gemini Vision inline base64 payload | `test_gemini_multimodal.py` 7/7 tests passed | ✅ PASSED |
| **Working Tree Cleanliness** | Không sót code tạm/mock/stubs | `git status -s` sạch 100% | ✅ PASSED |

---

## 2. Chi Tiết Xác Minh Từng Must-Have Theo 4 Kế Hoạch

### Plan 07-01: ExtractedImage Model, Parser Extractor & Ingestion Pipeline
- [x] **Must-Have 1: Model `ExtractedImage` được định nghĩa đầy đủ khóa ngoại và index.**
  - **Minh chứng mã nguồn:** [backend/app/database/models.py](file:///D:/KhacNghia/RAG/backend/app/database/models.py#L230-L251) định nghĩa bảng `extracted_images` với khóa chính UUID, khóa ngoại `source_version_id` (với `ondelete="CASCADE"`) và `dataset_id`. Đánh index kép `ix_extracted_images_dataset_source` và `ix_extracted_images_source_page`.
  - **Migration:** [backend/alembic/versions/0006_extracted_images.py](file:///D:/KhacNghia/RAG/backend/alembic/versions/0006_extracted_images.py) được đồng bộ đầy đủ.
- [x] **Must-Have 2: `ImageExtractor` xử lý được cả PDF và DOCX, có fallback render trang scan thành ảnh chất lượng cao.**
  - **Minh chứng mã nguồn:** [backend/app/rag/parsers/image_extractor.py](file:///D:/KhacNghia/RAG/backend/app/rag/parsers/image_extractor.py) triển khai trích xuất ảnh nhúng PDF qua `pypdfium2` và ảnh DOCX qua `zipfile` + Pillow. Khi trang PDF scan/chụp màn hình có selectable text < 50 ký tự (`FALLBACK_TEXT_THRESHOLD`), dịch vụ tự động render toàn trang với `scale=2.0` (150-200 DPI) lưu dạng `rendered_page` (D-02). Bỏ qua icon < 64px và resize ảnh > 1600px để chống DoS (T-07-02).
  - **Kiểm thử:** `tests/unit/test_image_extractor.py` (5/5 tests passed).
- [x] **Must-Have 3: Celery worker tự động lưu ảnh vào `storage/extracted_images/` và ghi metadata vào database.**
  - **Minh chứng mã nguồn:** [backend/app/workers/tasks.py](file:///D:/KhacNghia/RAG/backend/app/workers/tasks.py#L170-L305) và [backend/app/worker.py](file:///D:/KhacNghia/RAG/backend/app/worker.py) lưu ảnh vào `storage/extracted_images/{dataset_id}/{source_version_id}/{image_id}.png`. Đảm bảo tính idempotent khi retry bằng cách xóa bản ghi cũ trước khi nạp mới, và tự động liên kết `image_id` vào `CanonicalRecord.locator_data` và `record_metadata`.

### Plan 07-02: ACL-Fenced Image Serving API & Live Scope Recheck
- [x] **Must-Have 4: Endpoint ảnh yêu cầu xác thực JWT và kiểm tra quyền dataset.**
  - **Minh chứng mã nguồn:** [backend/app/api/images.py](file:///D:/KhacNghia/RAG/backend/app/api/images.py) định nghĩa `GET /api/v1/datasets/{dataset_id}/sources/{source_id}/images/{image_id}` với `get_current_active_account` và `verify_dataset_access`. Bắt buộc khớp đồng thời `ExtractedImage.id`, `dataset_id`, và `SourceVersion.source_id` để triệt tiêu lỗ hổng IDOR/Cross-Tenant (T-07-02).
- [x] **Must-Have 5: Thu hồi quyền dataset chặn tức thời mọi yêu cầu tải ảnh (Live Scope Recheck 403).**
  - **Minh chứng mã nguồn:** `verify_dataset_access` truy vấn trực tiếp bảng `dataset_grants` tại thời điểm yêu cầu. Khi quyền bị thu hồi, API lập tức trả về HTTP 403 Forbidden.
  - **Kiểm thử:** `tests/integration/test_image_api_security.py::test_live_scope_recheck_revocation` PASSED.
- [x] **Must-Have 6: Header bảo mật `private` và `nosniff` được đính kèm vào response.**
  - **Minh chứng mã nguồn:** `FileResponse` trả về `Cache-Control: private, max-age=3600` và `X-Content-Type-Options: nosniff`. Middleware bảo mật trong [backend/app/main.py](file:///D:/KhacNghia/RAG/backend/app/main.py#L90-L98) được tinh chỉnh bảo toàn header cache chuyên biệt cho tệp ảnh.

### Plan 07-03: Multimodal RAG Retrieval & Gemini Vision Generation
- [x] **Must-Have 7: Retrieval liên kết chính xác chunk với ảnh trích xuất của trang đó.**
  - **Minh chứng mã nguồn:** [backend/app/rag/retrieval.py](file:///D:/KhacNghia/RAG/backend/app/rag/retrieval.py#L8-L137) cung cấp `enrich_chunks_with_images` và `extract_representative_images`. Tích hợp trong `execute_hybrid_retrieval` tại [backend/app/database/retrieval.py](file:///D:/KhacNghia/RAG/backend/app/database/retrieval.py) để tự động làm giàu chunk với ảnh cùng trang/nguồn, có bộ lọc `dataset_id` ngăn rò rỉ ranh giới dữ liệu (T-07-05).
- [x] **Must-Have 8: Gemini nhận payload multimodal ảnh base64 trực tiếp và trả lời kèm trích dẫn ảnh.**
  - **Minh chứng mã nguồn:** [backend/app/providers/openai_llm.py](file:///D:/KhacNghia/RAG/backend/app/providers/openai_llm.py#L50-L126) triển khai `prepare_multimodal_images` và `build_multimodal_messages`. Đọc ảnh từ đĩa và mã hóa base64 chuẩn UTF-8 gửi qua cấu trúc `image_url: {"url": "data:image/png;base64,..."}`. System prompt được hướng dẫn chi tiết về việc đọc thông số kỹ thuật/sơ đồ và chèn trích dẫn Markdown `![Mô tả ảnh](IMAGE_API_URL)`. Chat API lưu trữ thông tin ảnh vào `ChatMessage.citations` và cung cấp qua `/api/v1/chat/citations/preview`.
- [x] **Must-Have 9: Bounded image limit (max 3 ảnh) giữ latency ổn định.**
  - **Minh chứng mã nguồn:** Giới hạn cứng tối đa 3 ảnh tiêu biểu (`images[:3]`) trong cả `prepare_multimodal_images` và `extract_representative_images`, bảo vệ latency và token budget (T-07-04, D-03).
  - **Kiểm thử:** `tests/unit/test_gemini_multimodal.py::test_multimodal_image_limit_enforced_to_max_3` PASSED.

### Plan 07-04: Frontend Image Citations, Evidence Preview & Lightbox Modal
- [x] **Must-Have 10: Panel EvidencePreview hiển thị ảnh trích dẫn khi click thẻ [1], [2].**
  - **Minh chứng mã nguồn:** [frontend/src/components/EvidencePreview.tsx](file:///D:/KhacNghia/RAG/frontend/src/components/EvidencePreview.tsx#L183-L274) hiển thị khối ảnh trích dẫn nằm giữa Tọa độ nguồn và Đoạn trích nguyên bản. Hỗ trợ hiển thị thumbnail `maxHeight: 260px`, `cursor: zoom-in`, nút "🔍 Phóng to chi tiết (Xem kích thước gốc)", và xử lý thân thiện lỗi tải ảnh/thu hồi quyền.
- [x] **Must-Have 11: Khung Chat hiển thị ảnh thumbnail trong câu trả lời của trợ lý.**
  - **Minh chứng mã nguồn:** [frontend/src/app/(workspace)/chat/page.tsx](file:///D:/KhacNghia/RAG/frontend/src/app/%28workspace%29/chat/page.tsx#L35-L124) triển khai `renderMessageContent` phân tích cú pháp Markdown image `![alt](url)`. Áp dụng hàm khử trùng URL `isSafeImageUrl(url)` chỉ chấp nhận các URL nội bộ hợp lệ `/api/v1/datasets/`, loại trừ nguy cơ XSS (T-07-06). Bổ sung khối gallery ảnh trích dẫn dưới phản hồi của trợ lý.
- [x] **Must-Have 12: Modal Lightbox hỗ trợ zoom in, zoom out và xem độ nét cao của sơ đồ kỹ thuật.**
  - **Minh chứng mã nguồn:** [frontend/src/components/ImageLightboxModal.tsx](file:///D:/KhacNghia/RAG/frontend/src/components/ImageLightboxModal.tsx) tạo modal overlay toàn màn hình với nền tối mờ (`rgba(15, 23, 42, 0.88)`). Hỗ trợ phóng to (+), thu nhỏ (-), đặt lại 1:1, cuộn chuột zoom, kéo di chuyển (drag & pan), khóa cuộn trang nền và phím tắt `Escape`.

---

## 3. Đối Chiếu Requirements (Traceability)

| Requirement ID | Định nghĩa & Mô tả | Trạng thái Phase 7 | Bằng chứng kiểm tra |
|---|---|---|---|
| **DATA-02** | Nhập PDF, DOCX, CSV, XLSX, TXT, JSON, JSONL, .log; báo lỗi rõ ràng. Mở rộng trích xuất ảnh nhúng và render trang scan fallback. | **Hoàn thành xuất sắc** | `ImageExtractor` trích xuất embedded raster/vector images; tự động render trang scan fallback `scale=2.0` cho các tài liệu scan/chụp ảnh (D-02). |
| **DATA-03** | Quản lý trạng thái xử lý ingestion, retry không nhân đôi bản ghi, khôi phục sau restart. | **Hoàn thành xuất sắc** | Lưu trữ phân cấp `storage/extracted_images/{dataset_id}/{source_version_id}/`; dọn dẹp sạch bản ghi cũ khi worker retry đảm bảo idempotent tuyệt đối. |
| **RETR-03** | Truy xuất tri thức theo dataset và khoảng thời gian; trích dẫn bằng chứng đa phương thức (hình ảnh kèm số dòng/trang) và gửi vào prompt vision của Gemini. | **Hoàn thành xuất sắc** | RAG retriever làm giàu chunk với `ExtractedImage`, tuân thủ nghiêm ngặt dataset ACL, format inline base64 image gửi tới Gemini Vision API, và trả về trích dẫn ảnh trên giao diện Chat & EvidencePreview. |

---

## 4. Kiểm Tra Liên Kết Hệ Thống & Triệt Tiêu Mã Giả (No Mocks/Stubs in Production)

1. **Ranh giới kiến trúc Clean Architecture:**
   - `backend/app/rag/parsers/image_extractor.py` hoạt động độc lập ở tầng parser, không phụ thuộc database models hay FastAPI request handlers.
   - Các API endpoints sử dụng dependency injection tiêu chuẩn (`get_db`, `get_current_active_account`, `verify_dataset_access`).
2. **Loại bỏ hoàn toàn stub/mock trong mã nguồn production:**
   - Không tồn tại placeholder `pass`, `NotImplementedError`, dữ liệu mock hay hardcoded UUID nào trong các module nghiệp vụ `image_extractor.py`, `images.py`, `retrieval.py`, `openai_llm.py`, `chat.py`, `EvidencePreview.tsx`, `ImageLightboxModal.tsx`.
   - Các mock adapters (`FakeLLMAdapter`) được cô lập chặt chẽ trong `backend/app/providers/fake.py` và chỉ phục vụ môi trường kiểm thử unit tests.

---

## 5. Kết Luận

Phase 07 đã đạt được 100% mục tiêu đề ra:
- Khả năng trích xuất hình ảnh đa phương thức tự động từ PDF và DOCX hoạt động trơn tru với cơ chế fallback thông minh cho tài liệu scan.
- Kiểm soát phân quyền bảo mật chặt chẽ theo ASVS L1 với cơ chế Live Scope Recheck cho hình ảnh.
- Tích hợp trực tiếp Google Gemini Multimodal Vision qua định dạng base64 chuẩn OpenAI/Gemini.
- Trải nghiệm giao diện trực quan hoàn thiện với hiển thị kép (Dual Display) trong Chat và Panel EvidencePreview, kết hợp Modal phóng to chi tiết Lightbox Pan/Zoom.
- Toàn bộ 244 bài kiểm thử backend và bản build Next.js Turbopack đều vượt qua với kết quả tuyệt đối.

## Verification Complete.

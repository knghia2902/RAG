# Phase 07: Multimodal Document Image Extraction and Citations - Context

**Gathered:** 2026-10-15
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 7 mở rộng năng lực RAG cho tài liệu kỹ thuật/logistics sang dạng đa phương thức (Multimodal): trích xuất tự động hình ảnh/sơ đồ nhúng từ PDF và DOCX (kể cả tài liệu chụp màn hình/scan), lưu trữ cục bộ bảo mật theo phân quyền dataset ACL, đưa hình ảnh liên quan trực tiếp vào Google Gemini Vision để suy luận phân tích, và hiển thị ảnh trực quan kèm số dòng/trang trích dẫn trong câu trả lời Chat và bảng xem bằng chứng (EvidencePreview).

Phase này tập trung vào trích xuất, lưu trữ bảo mật, RAG đa phương thức và trải nghiệm hiển thị hình ảnh trích dẫn. Các tính năng OCR nhận diện chữ viết tay hay tự động chỉnh sửa ảnh nâng cao không thuộc phạm vi phase này.

</domain>

<decisions>
## Implementation Decisions

### Cơ chế trích xuất ảnh và xử lý tài liệu (Extraction & Document Handling)
- **D-01:** Trích xuất tự động toàn bộ hình ảnh nhúng (embedded raster/vector images: sơ đồ kết nối, hình ảnh giao diện, bảng ảnh trong datasheet) trong file PDF và DOCX, lưu trữ tọa độ trang (`page`), thứ tự và liên kết với đoạn văn bản ngữ cảnh xung quanh.
- **D-02:** Đối với file PDF không có text layer hoặc là bản scan/chụp màn hình (như tài liệu `2.Cài Đặt Esxi Host.pdf` in từ web), hệ thống tự động render từng trang thành ảnh chất lượng cao để lưu trữ và lập chỉ mục trang thay vì từ chối với lỗi không có text, giúp kỹ thuật viên không bị mất tài liệu và vẫn xem được toàn bộ nội dung trực quan.

### Đưa ảnh vào quy trình LLM Gemini (Multimodal Vision Integration)
- **D-03:** Tận dụng khả năng Multimodal Vision bản địa của Google Gemini (`gemini-flash-lite-latest` hoặc endpoint tương thích). Khi RAG tìm thấy các đoạn trích dẫn (evidence chunks) có liên kết hình ảnh liên quan, hệ thống gửi trực tiếp hình ảnh (base64 inline image part, có giới hạn tối đa 2-3 ảnh liên quan nhất để tiết kiệm token và độ trễ) cùng với ngữ cảnh văn bản vào prompt.
- **D-04:** Gemini được chỉ định đối chiếu trực tiếp chi tiết trong ảnh (sơ đồ khối, sơ đồ mạng, bảng thông số, trạng thái cấu hình trên màn hình chụp) để trả lời câu hỏi và sinh liên kết trích dẫn ảnh rõ ràng (`![Mô tả ảnh](image_id)`).

### Trải nghiệm hiển thị trên Giao diện Web (UI & Citation Preview)
- **D-05:** **Hiển thị kép (Dual Display):**
  - Trong khung Chat: Hiển thị ảnh thu nhỏ (thumbnail) ngay trong câu trả lời của AI ở các đoạn trích dẫn hoặc phần mô tả sơ đồ, hỗ trợ click phóng to (lightbox modal).
  - Trong panel Bằng chứng trích dẫn (`EvidencePreview`): Khi kỹ thuật viên click vào thẻ trích dẫn `[1]`, `[2]`, panel bên phải hiển thị rõ ràng hình ảnh trích dẫn ở ngay dưới tọa độ nguồn (Trang X, Dòng Y-Z, Mục...) và đoạn trích văn bản nguyên bản.
- **D-06:** Hỗ trợ tính năng xem ảnh chất lượng cao: zoom in, zoom out, xem kích thước gốc để kỹ thuật viên đọc rõ các thông số kỹ thuật nhỏ hoặc tên cổng mạng/thiết bị trong sơ đồ.

### Lưu trữ và Bảo mật phân quyền ảnh (Storage & Dataset ACL)
- **D-07:** Hình ảnh trích xuất được lưu trữ cục bộ trên volume Docker của backend/worker theo đường dẫn phân cấp an toàn: `storage/extracted_images/{dataset_id}/{source_version_id}/{image_id}.png`.
- **D-08:** Tuyệt đối không phục vụ ảnh qua URL tĩnh công khai. Mọi yêu cầu lấy ảnh phải đi qua API endpoint bảo mật (ví dụ: `/api/v1/datasets/{dataset_id}/sources/{source_id}/images/{image_id}`), bắt buộc xác thực JWT session và kiểm tra quyền truy cập dataset hiện tại của người dùng (Live Scope Recheck). Nếu người dùng bị thu hồi quyền dataset, API lập tức từ chối trả về ảnh.
- **D-09:** Chuẩn hóa định dạng và kích thước ảnh (tối ưu hóa kích thước tối đa, chuyển đổi định dạng tối ưu như PNG/WebP chất lượng cao) nhằm tiết kiệm không gian lưu trữ và tăng tốc độ tải mà vẫn giữ độ sắc nét của chữ trong ảnh kỹ thuật.

### the agent's Discretion
- **D-10:** Lựa chọn thư viện trích xuất ảnh tối ưu (kết hợp pypdfium2 / PyMuPDF `fitz` hoặc Docling image export) trong worker pipeline để đạt tốc độ xử lý cao nhất.
- **D-11:** Thiết kế cơ chế tính điểm liên quan (relevance scoring) giữa câu hỏi người dùng và các hình ảnh trích xuất trong tài liệu để chọn top 2-3 ảnh phù hợp nhất khi gửi tới Gemini.

</decisions>

<specifics>
## Specific Ideas

- Người dùng yêu cầu cụ thể: *"Phần trả lời có thể thêm hình ảnh nếu datasheet có hình ảnh không với trích dẫn mình muốn trích dẫn với dòng và có hình ảnh ở đó"*.
- Điển hình từ thực tế: Khi kỹ thuật viên tải lên tài liệu hướng dẫn cài đặt ESXi (file in từ web, các bước là ảnh chụp màn hình giao diện cấu hình mạng và ổ đĩa), hệ thống cần hiển thị được ảnh chụp màn hình tương ứng với bước cấu hình và dòng trích dẫn để kỹ thuật viên làm theo.

</specifics>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing:**

### Core Project Specifications
- `.planning/PROJECT.md` — RAG for logistics IT, local storage, OpenAI embedding, Gemini LLM, dataset ACL boundaries.
- `.planning/ROADMAP.md` — Phase 7 roadmap entry, dependencies, and success criteria.
- `.planning/REQUIREMENTS.md` — DATA-02, DATA-03 (provenance coordinates), RETR-03 (grounded evidence citations).

### Codebase Implementations & Adapters
- `backend/app/rag/parsers/docling_adapter.py` — Hiện tại parse PDF/DOCX với `do_ocr=False` và `generate_page_images=False`. Cần mở rộng hoặc tích hợp thêm bộ trích xuất ảnh.
- `backend/app/database/models.py` — Các models `SourceVersion`, `CanonicalRecord`, `ChatMessage`. Cần bảng hoặc trường metadata lưu trữ thông tin hình ảnh trích xuất (`ExtractedImage` hoặc metadata trong record).
- `backend/app/providers/openai_llm.py` — Lớp giao tiếp LLM hiện tại (OpenAI-compatible cho Gemini). Cần hỗ trợ gửi multimodal content parts (text + image_url / inline_data).
- `backend/app/worker.py` — Quy trình ingestion chạy nền trong Celery worker xử lý trích xuất tài liệu.
- `frontend/src/components/EvidencePreview.tsx` — Modal/panel xem trước bằng chứng nguồn, hiện đã hiển thị tọa độ (trang, dòng, mục) và văn bản trích dẫn. Cần bổ sung khung hiển thị hình ảnh kèm zoom/lightbox.
- `frontend/src/app/(workspace)/chat/page.tsx` — Giao diện chat, cần hỗ trợ hiển thị ảnh đính kèm câu trả lời từ assistant.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `DoclingAdapter` & `pypdfium2`: Có sẵn trong backend và worker container, có khả năng render trang PDF thành bitmap/ảnh hoặc trích xuất embedded images.
- `EvidencePreview.tsx`: Thành phần giao diện đã hoàn thiện đầy đủ logic Live Scope Recheck, hiển thị số dòng/trang, nhãn dataset và trạng thái loading/revocation.
- `OpenAILLMProvider`: Đã cấu hình kết nối tới Google Gemini (`https://generativelanguage.googleapis.com/v1beta/openai/`) sử dụng model `gemini-flash-lite-latest`.

### Established Patterns
- **Dataset ACL & Live Scope Recheck:** Mọi endpoint truy cập dữ liệu nguồn hoặc bằng chứng phải qua `get_current_active_account` và xác thực `DatasetGrant`. Ảnh cũng phải tuân thủ nghiêm ngặt mô hình này.
- **Local Storage Isolation:** Dữ liệu file được lưu trong `storage/` mount vào Docker container, không đưa ra public static path.
- **Asynchronous Ingestion:** Việc xử lý file nặng (render ảnh, nén ảnh) được thực hiện trong Celery worker tách biệt với API chính.

### Integration Points
- Backend Ingestion: Thêm bước trích xuất/lưu ảnh trong `backend/app/worker.py` và liên kết với `CanonicalRecord`.
- Database: Lưu thông tin ảnh (image_id, source_version_id, page, bounding_box, storage_path, mime_type, caption/description).
- Backend Image API: Thêm endpoint `GET /api/v1/datasets/{dataset_id}/sources/{source_id}/images/{image_id}` có kiểm tra quyền.
- LLM Provider: Bổ sung khả năng format multimodal message payloads cho Gemini trong `OpenAILLMProvider`.
- Frontend: Nâng cấp `EvidencePreview.tsx` và Markdown renderer trong Chat để hiển thị hình ảnh với token xác thực hoặc cookie session an toàn.

</code_context>

<deferred>
## Deferred Ideas

- OCR nhận diện chữ viết tay / tài liệu scan văn bản dày đặc bằng mô hình OCR chuyên dụng nội bộ (thuộc backlog v2 khi chuyển đổi sang kiến trúc Agent/Tool đầy đủ).
- Công cụ vẽ chú thích / đo đạc trực tiếp trên sơ đồ kỹ thuật (Vector annotation tool trên web).

</deferred>

---

*Phase: 07-multimodal-document-image-extraction-and-citations*
*Context gathered: 2026-10-15*

# Phase 07: Multimodal Document Image Extraction and Citations - Pattern Map

**Mapped:** 2026-10-15  
**Files analyzed:** 8  
**Analogs found:** 8 / 8  

---

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|---|---|---|---|---|
| `backend/app/rag/parsers/image_extractor.py` | parser/extractor | file bytes → extracted images & metadata | `backend/app/rag/parsers/docling_adapter.py` | exact |
| `backend/app/database/models.py` (`ExtractedImage`) | database model | schema & persistence for image metadata | `backend/app/database/models.py` (`CanonicalRecord`) | exact |
| `backend/app/worker.py` | Celery ingestion task | background parsing, rendering & storage | `backend/app/worker.py` | exact |
| `backend/app/api/images.py` | REST API router | secure image delivery with ACL check | `backend/app/api/sources.py` | exact |
| `backend/app/providers/openai_llm.py` | LLM client provider | multimodal message format for Gemini | `backend/app/providers/openai_llm.py` | exact |
| `backend/app/rag/retrieval.py` | RAG retrieval service | chunk lookup with associated images | `backend/app/rag/retrieval.py` | exact |
| `frontend/src/components/EvidencePreview.tsx` | UI component | image citation preview & coordinates | `frontend/src/components/EvidencePreview.tsx` | exact |
| `frontend/src/components/ImageLightboxModal.tsx` | UI modal component | image pan/zoom and inspect | `frontend/src/components/Navbar.tsx` | role-match |

---

## Pattern Assignments

### 1. Parser & Image Extraction Pattern (`backend/app/rag/parsers/image_extractor.py`)

**Analog:** `backend/app/rag/parsers/docling_adapter.py` & `pypdfium2` fallback
**Rules:**
- Xử lý file PDF: dùng `pypdfium2.PdfDocument(io.BytesIO(content))`.
- Duyệt qua từng trang: nếu trang có embedded images, trích xuất bitmap; nếu trang không có text hoặc là trang scan/chụp toàn trang, render toàn trang với `page.render(scale=2.0).to_pil()`.
- Xử lý file DOCX: mở qua `zipfile.ZipFile(io.BytesIO(content))`, lọc các file trong `word/media/`, đọc bytes và mime-type.
- Lưu ảnh chuẩn hóa WebP/PNG bằng PIL, tính toán hash SHA256 và kích thước width x height.

### 2. Database Model Pattern (`backend/app/database/models.py`)

**Analog:** `CanonicalRecord` & `SourceVersion`
**Rules:**
- Tạo class `ExtractedImage(Base)` kế thừa SQLAlchemy Base.
- Bắt buộc có foreign key tới `source_versions.id` (với `ondelete="CASCADE"`) và `datasets.id`.
- Chứa các cột: `id`, `source_version_id`, `dataset_id`, `page_number`, `image_type`, `storage_path`, `mime_type`, `width`, `height`, `caption`, `created_at`.
- Đánh chỉ mục Index trên `(dataset_id, source_version_id)` và `(source_version_id, page_number)`.

### 3. ACL Image Serving Endpoint Pattern (`backend/app/api/images.py`)

**Analog:** `backend/app/api/sources.py` (`download_source`)
**Rules:**
- Nhận tham số `dataset_id`, `source_id`, `image_id`.
- Tiêm phụ thuộc `account = Depends(get_current_active_account)` và `db = Depends(get_db)`.
- Gọi hàm `verify_dataset_access(account, dataset_id, db)` đầu tiên để thực hiện Live Scope Recheck.
- Nếu không có quyền, quăng lỗi `HTTPException(status_code=403, detail="Tài khoản không có quyền truy cập dataset này.")`.
- Trả về `FileResponse(path, media_type, headers={"Cache-Control": "private, max-age=3600"})`.

### 4. Multimodal Generation Pattern (`backend/app/providers/openai_llm.py`)

**Analog:** `OpenAILLMProvider.generate_grounded_answer`
**Rules:**
- Mở rộng signature nhận `images: list[ExtractedImageData] | None = None`.
- Nếu có `images`: xây dựng user message content dưới dạng danh sách `[{"type": "text", ...}, {"type": "image_url", "image_url": {"url": "data:image/png;base64,..."}}]`.
- Giới hạn tối đa 3 ảnh liên quan nhất để không tràn token budget và kiểm soát latency p95 dưới 30s.

### 5. Frontend Lightbox & Evidence Display Pattern (`frontend/src/components/`)

**Analog:** `frontend/src/components/EvidencePreview.tsx`
**Rules:**
- Thêm trường `image_id?: string; image_url?: string;` vào interface `CitationPreviewDetail`.
- Khi có `image_url`, render container `<img>` với thuộc tính `loading="lazy"` và xử lý sự kiện `onClick` để mở `ImageLightboxModal`.
- `ImageLightboxModal` là fixed portal overlay có nút đóng, zoom in, zoom out và reset zoom.

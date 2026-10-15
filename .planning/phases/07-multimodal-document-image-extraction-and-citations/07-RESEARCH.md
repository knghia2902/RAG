# Phase 07: Multimodal Document Image Extraction and Citations - Research

**Researched:** 2026-10-15
**Domain:** Document Image Extraction, Multimodal Vision RAG, Local Storage & ACL-Fenced Image Delivery, Frontend Image Citations
**Confidence:** HIGH

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- **D-01 (Embedded Image Extraction):** Trích xuất tự động toàn bộ hình ảnh nhúng (embedded raster/vector images: sơ đồ kết nối, hình ảnh giao diện, bảng ảnh trong datasheet) trong file PDF và DOCX, lưu trữ tọa độ trang (`page`), thứ tự và liên kết với đoạn văn bản ngữ cảnh xung quanh.
- **D-02 (Rendered Page Fallback for Scans/Screenshots):** Đối với file PDF không có text layer hoặc là bản scan/chụp màn hình (như tài liệu `2.Cài Đặt Esxi Host.pdf` in từ web), hệ thống tự động render từng trang thành ảnh chất lượng cao để lưu trữ và lập chỉ mục trang thay vì từ chối với lỗi không có text, giúp kỹ thuật viên không bị mất tài liệu và vẫn xem được toàn bộ nội dung trực quan.
- **D-03 (Gemini Multimodal Vision Integration):** Tận dụng khả năng Multimodal Vision bản địa của Google Gemini (`gemini-flash-lite-latest` hoặc endpoint tương thích). Khi RAG tìm thấy các đoạn trích dẫn (evidence chunks) có liên kết hình ảnh liên quan, hệ thống gửi trực tiếp hình ảnh (base64 inline image part, có giới hạn tối đa 2-3 ảnh liên quan nhất để tiết kiệm token và độ trễ) cùng với ngữ cảnh văn bản vào prompt.
- **D-04 (Vision-Guided Grounded Citations):** Gemini được chỉ định đối chiếu trực tiếp chi tiết trong ảnh (sơ đồ khối, sơ đồ mạng, bảng thông số, trạng thái cấu hình trên màn hình chụp) để trả lời câu hỏi và sinh liên kết trích dẫn ảnh rõ ràng (`![Mô tả ảnh](image_id)`).
- **D-05 (Dual UI Display - Chat & Citation Modal):**
  - Trong khung Chat: Hiển thị ảnh thu nhỏ (thumbnail) ngay trong câu trả lời của AI ở các đoạn trích dẫn hoặc phần mô tả sơ đồ, hỗ trợ click phóng to (lightbox modal).
  - Trong panel Bằng chứng trích dẫn (`EvidencePreview`): Khi kỹ thuật viên click vào thẻ trích dẫn `[1]`, `[2]`, panel bên phải hiển thị rõ ràng hình ảnh trích dẫn ở ngay dưới tọa độ nguồn (Trang X, Dòng Y-Z, Mục...) và đoạn trích văn bản nguyên bản.
- **D-06 (Image Zoom & Inspection):** Hỗ trợ tính năng xem ảnh chất lượng cao: zoom in, zoom out, xem kích thước gốc để kỹ thuật viên đọc rõ các thông số kỹ thuật nhỏ hoặc tên cổng mạng/thiết bị trong sơ đồ.
- **D-07 (Local Structured Storage):** Hình ảnh trích xuất được lưu trữ cục bộ trên volume Docker của backend/worker theo đường dẫn phân cấp an toàn: `storage/extracted_images/{dataset_id}/{source_version_id}/{image_id}.png`.
- **D-08 (Strict ACL-Fenced Image Serving):** Tuyệt đối không phục vụ ảnh qua URL tĩnh công khai. Mọi yêu cầu lấy ảnh phải đi qua API endpoint bảo mật (ví dụ: `/api/v1/datasets/{dataset_id}/sources/{source_id}/images/{image_id}`), bắt buộc xác thực JWT session và kiểm tra quyền truy cập dataset hiện tại của người dùng (Live Scope Recheck). Nếu người dùng bị thu hồi quyền dataset, API lập tức từ chối trả về ảnh với HTTP 403 Forbidden.
- **D-09 (Image Normalization & Optimization):** Chuẩn hóa định dạng và kích thước ảnh (tối ưu hóa kích thước tối đa, chuyển đổi định dạng tối ưu như PNG/WebP chất lượng cao) nhằm tiết kiệm không gian lưu trữ và tăng tốc độ tải mà vẫn giữ độ sắc nét của chữ trong ảnh kỹ thuật.

### the agent's Discretion

- **D-10:** Lựa chọn thư viện trích xuất ảnh tối ưu (kết hợp pypdfium2 / PyMuPDF `fitz` hoặc Docling image export) trong worker pipeline để đạt tốc độ xử lý cao nhất.
- **D-11:** Thiết kế cơ chế tính điểm liên quan (relevance scoring) giữa câu hỏi người dùng và các hình ảnh trích xuất trong tài liệu để chọn top 2-3 ảnh phù hợp nhất khi gửi tới Gemini.

### Deferred Ideas (OUT OF SCOPE)

- OCR nhận diện chữ viết tay / tài liệu scan văn bản dày đặc bằng mô hình OCR chuyên dụng nội bộ (thuộc backlog v2 khi chuyển đổi sang kiến trúc Agent/Tool đầy đủ).
- Công cụ vẽ chú thích / đo đạc trực tiếp trên sơ đồ kỹ thuật (Vector annotation tool trên web).

</user_constraints>

<architectural_responsibility_map>
## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| PDF/DOCX Image Extraction & Page Rendering | Backend Celery Worker (`app/worker.py`, `app/rag/parsers/`) | Local Storage Volume (`storage/extracted_images/`) | Xử lý file nặng không làm nghẽn API server, render offline bằng pypdfium2/zipfile. |
| Extracted Image Metadata & Chunk Association | PostgreSQL Database (`app/database/models.py`) | Canonical Records / Evidence Chunks | Lưu trữ metadata ảnh, liên kết chặt chẽ với `SourceVersion` và `CanonicalRecord` theo `dataset_id`. |
| ACL-Fenced Image Delivery API | FastAPI Application (`app/api/datasets.py` hoặc `images.py`) | Auth Middleware & Dataset ACL | Kiểm tra quyền JWT và Live Scope Recheck trước khi stream file ảnh cục bộ, ngăn chặn rò rỉ ranh giới dataset. |
| Multimodal Prompt Construction & Gemini Vision | LLM Provider (`app/providers/openai_llm.py`) | RAG Retrieval Service (`app/rag/retrieval.py`) | Format payload chứa inline base64 image data theo chuẩn OpenAI/Gemini Vision API. |
| Dual Display & Lightbox Modal | Frontend Web Client (`EvidencePreview.tsx`, `chat/page.tsx`) | Browser Storage / Session Cookie | Hiển thị thumbnail trong chat và ảnh chi tiết kèm zoom/pan trong panel trích dẫn bằng chứng. |

</architectural_responsibility_map>

<research_summary>
## Summary

Nghiên cứu cho thấy kiến trúc hiện tại của dự án (FastAPI + Celery + PostgreSQL/pgvector + Next.js + Google Gemini) hoàn toàn sẵn sàng để nâng cấp lên tính năng đa phương thức (Multimodal RAG):
1. **Công nghệ trích xuất ảnh:** Thư viện `pypdfium2` và `PIL` (Pillow) đã có sẵn trong container `backend` và `worker`. `pypdfium2` có khả năng vừa trích xuất embedded images, vừa render trang PDF thành ảnh bitmap chất lượng cao với tốc độ vượt trội (vài mili-giây/trang) mà không đòi hỏi bất kỳ model tải ngoài nào. Đối với `.docx`, cấu trúc OOXML là file zip tiêu chuẩn, cho phép trích xuất ảnh nhúng trong thư mục `word/media/` với độ tin cậy tuyệt đối.
2. **Tích hợp Gemini Multimodal Vision:** Endpoint OpenAI-compatible của Google Gemini (`https://generativelanguage.googleapis.com/v1beta/openai/`) hỗ trợ đầy đủ schema payload `image_url` với `data:image/png;base64,{base64_data}`. Điều này cho phép mở rộng `OpenAILLMProvider` để đưa trực tiếp ảnh sơ đồ/màn hình cấu hình vào prompt mà không cần thay đổi client SDK.
3. **Bảo mật và Phân quyền:** Tuân thủ nguyên tắc cách ly dữ liệu: Ảnh được lưu trữ trên local disk volume theo đường dẫn `storage/extracted_images/{dataset_id}/{source_version_id}/{image_id}.png`. Endpoint phục vụ ảnh áp dụng `get_current_active_account` và `verify_dataset_access`, đảm bảo không bao giờ lộ URL tĩnh ra ngoài.
4. **Trải nghiệm người dùng:** Giao diện `EvidencePreview.tsx` được bổ sung khung ảnh trích dẫn trực quan dưới tọa độ dòng/trang, hỗ trợ modal phóng to (Lightbox Zoom) phục vụ đọc sơ đồ mạng và bảng thông số datasheet.

</research_summary>

<standard_stack>
## Standard Stack

### Core
| Library / Tool | Version | Purpose | Why Standard |
|----------------|---------|---------|--------------|
| `pypdfium2` | Đã có trong container (backend/worker) | Render trang PDF & trích xuất bitmap offline | Hiệu năng C++ cực nhanh, 100% offline, không cần Poppler/Ghostscript. |
| `Pillow` (PIL) | Đã có trong container | Chuẩn hóa, nén WebP/PNG, kiểm tra kích thước ảnh | Tiêu chuẩn xử lý ảnh số 1 trong Python, nhẹ và ổn định. |
| `python-docx` / `zipfile` | Stdlib / Đã có trong container | Trích xuất hình ảnh nhúng từ tệp DOCX | Đọc trực tiếp phần media OOXML không mất mát dữ liệu. |
| `Google Gemini API` (`gemini-flash-lite-latest`) | Via OpenAI-compatible endpoint | Nhận diện & phân tích hình ảnh kỹ thuật | Hỗ trợ multimodal vision tốc độ cao, chi phí rẻ và khả năng đọc chữ trong ảnh tốt. |
| `FastAPI FileResponse` | 0.142.2 | Stream dữ liệu ảnh có xác thực bảo mật | Tích hợp streaming không tốn RAM server, hỗ trợ Cache-Control và Content-Type. |

### Supporting
| Component | Location | Purpose | When to Use |
|-----------|----------|---------|-------------|
| `backend/app/rag/parsers/image_extractor.py` | Parser module | Trích xuất ảnh từ PDF/DOCX và render trang fallback | Được gọi bởi Celery ingestion worker khi nạp tài liệu. |
| `backend/app/database/models.py` (`ExtractedImage`) | Database model | Lưu metadata của ảnh (kích thước, vị trí trang, đường dẫn file, hash) | Quản lý vòng đời và liên kết ảnh với CanonicalRecord. |
| `backend/app/api/images.py` | API Router | Endpoint bảo mật phục vụ ảnh cho frontend | Khi client yêu cầu tải ảnh trong Chat hoặc EvidencePreview. |
| `frontend/src/components/EvidencePreview.tsx` | UI Component | Panel xem trước bằng chứng nguồn có ảnh | Khi người dùng click thẻ trích dẫn [1], [2]. |
| `frontend/src/components/ImageLightboxModal.tsx` | UI Component | Modal phóng to ảnh và thu phóng chi tiết | Khi người dùng click vào ảnh trong Chat hoặc EvidencePreview. |

</standard_stack>

<architecture_patterns>
## Architecture Patterns

### 1. Luồng xử lý trích xuất ảnh trong Ingestion Pipeline

```
[Uploaded File (PDF/DOCX)]
          │
          ▼
┌────────────────────────┐
│  Docling / PDF Adapter  │
└──────────┬─────────────┘
           │
           ├──────────────────────────────┬──────────────────────────────┐
           ▼                              ▼                              ▼
  [Văn bản có sẵn]             [Ảnh nhúng (Embedded)]          [Trang Scan / Chụp màn hình]
           │                              │                              │
           │                      Trích xuất qua                 Render toàn trang
           │                      pypdfium2/zipfile              bằng pypdfium2 (150 DPI)
           │                              │                              │
           ▼                              ▼                              ▼
   Tạo EvidenceChunk              Lưu vào storage/               Lưu vào storage/
           │                     Ghi `ExtractedImage`           Ghi `ExtractedImage`
           │                              │                              │
           └──────────────────────────────┴──────────────────────────────┘
                                          │
                                          ▼
                               Lưu `CanonicalRecord`
                       (locator_data kèm image_id, page)
                                          │
                                          ▼
                               Tạo Vector Embedding
                       (bao gồm cả mô tả trang ảnh)
```

### 2. Định dạng Multimodal Payload gửi tới Gemini API

```python
# Cấu trúc payload gửi tới client.chat.completions.create()
content_parts = [
    {
        "type": "text", 
        "text": f"Bối cảnh văn bản trích dẫn:\n{formatted_context}\n\nCâu hỏi: {user_query}"
    }
]

for img in relevant_images:
    base64_str = base64.b64encode(img.bytes).decode("utf-8")
    content_parts.append({
        "type": "image_url",
        "image_url": {
            "url": f"data:{img.mime_type};base64,{base64_str}"
        }
    })

messages = [
    {"role": "system", "content": SYSTEM_PROMPT_WITH_MULTIMODAL_INSTRUCTIONS},
    {"role": "user", "content": content_parts}
]
```

### 3. Cơ chế Bảo mật Phân quyền API Ảnh (Live Scope Recheck)

```python
@router.get("/datasets/{dataset_id}/sources/{source_id}/images/{image_id}")
async def get_extracted_image(
    dataset_id: uuid.UUID,
    source_id: uuid.UUID,
    image_id: uuid.UUID,
    db: Session = Depends(get_db),
    account: Account = Depends(get_current_active_account),
):
    # 1. Kiểm tra quyền truy cập dataset hiện tại của tài khoản
    verify_dataset_access(account, dataset_id, db)
    
    # 2. Kiểm tra ảnh có tồn tại và thuộc dataset_id không
    image_record = get_image_record(db, image_id, dataset_id, source_id)
    if not image_record or not os.path.exists(image_record.storage_path):
        raise HTTPException(status_code=404, detail="Không tìm thấy hình ảnh.")
        
    # 3. Trả về FileResponse với header bảo mật
    return FileResponse(
        path=image_record.storage_path,
        media_type=image_record.mime_type,
        headers={"Cache-Control": "private, max-age=3600"}
    )
```

</architecture_patterns>

<validation_architecture>
## Validation Architecture

### 1. Phân cấp kiểm thử
- **Unit Tests (`backend/tests/unit/`):**
  - Trích xuất ảnh nhúng từ file PDF/DOCX mẫu.
  - Render trang PDF scan thành file PNG với pypdfium2.
  - Mã hóa base64 và xây dựng multimodal payload tương thích Gemini.
- **Integration Tests (`backend/tests/integration/`):**
  - Worker ingestion lưu trữ file ảnh vào đúng thư mục `storage/extracted_images/{dataset_id}/...`.
  - API endpoint `/images/{image_id}` kiểm tra nghiêm ngặt quyền: 
    - Technician có quyền dataset: 200 OK kèm Content-Type.
    - Technician không có quyền dataset: 403 Forbidden.
    - Thu hồi quyền (Live Scope Recheck): lập tức trả về 403 Forbidden.
- **Acceptance Tests (`backend/tests/acceptance/`):**
  - Hỏi đáp RAG với tài liệu có sơ đồ/hình ảnh: Câu trả lời chứa trích dẫn ảnh (`![...](...)`) và panel EvidencePreview hiển thị đúng ảnh và số trang.
  - Tài liệu scan/chụp màn hình (như file ESXi) được lập chỉ mục thành công và có thể xem trực quan.

</validation_architecture>

---

*Phase: 07-multimodal-document-image-extraction-and-citations*
*Research completed: 2026-10-15*

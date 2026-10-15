import sys
from typing import Any, Callable, Sequence
from uuid import UUID
from app.rag.contracts import EmbeddingProvider, EvidenceChunk, RetrievalRequest, Retriever, SourceLocator
from app.rag.lexical import LexicalMatcher


def enrich_chunks_with_images(
    chunks: Sequence[EvidenceChunk],
    db: Any = None,
    image_lookup_fn: Callable[[UUID, UUID, int, int | None], list[dict]] | None = None,
    max_images_per_chunk: int = 2,
    max_total_images: int = 3,
) -> list[EvidenceChunk]:
    """Liên kết các đoạn bằng chứng (chunks) với các hình ảnh trích xuất tương ứng.
    
    Quy tắc liên kết:
    1. Với mỗi chunk, trích xuất (dataset_id, source_id, source_version, page).
    2. Nếu image_lookup_fn được truyền, gọi lookup function.
    3. Nếu db được truyền (SQLAlchemy Session), truy vấn bảng ExtractedImage khớp:
       - ExtractedImage.dataset_id == chunk.dataset_id (bảo vệ nghiêm ngặt ACL)
       - SourceVersion.source_id == chunk.locator.source_id
       - SourceVersion.version_number == chunk.locator.source_version
       - ExtractedImage.page_number == chunk.locator.page (nếu page có giá trị)
    4. Gán metadata ảnh vào trường images của EvidenceChunk.
    5. Giới hạn tối đa max_images_per_chunk ảnh cho mỗi chunk.
    """
    if not chunks:
        return []

    # If chunks already have images and no db/lookup provided, return as is
    if db is None and image_lookup_fn is None:
        return list(chunks)

    # If db is provided and no custom lookup, use dynamic lookup via db
    lookup = image_lookup_fn
    if lookup is None and db is not None:
        models = sys.modules.get("app.database.models")
        if not models:
            import importlib
            models = importlib.import_module("app.database.models")
        ExtractedImage = models.ExtractedImage
        SourceVersion = models.SourceVersion
        from sqlalchemy import select

        def _db_lookup(dataset_id: UUID, source_id: UUID, version_number: int, page: int | None) -> list[dict]:
            stmt = (
                select(ExtractedImage)
                .join(SourceVersion, ExtractedImage.source_version_id == SourceVersion.id)
                .where(
                    ExtractedImage.dataset_id == dataset_id,
                    SourceVersion.source_id == source_id,
                    SourceVersion.version_number == version_number,
                )
            )
            if page is not None:
                stmt = stmt.where(ExtractedImage.page_number == page)
            stmt = stmt.order_by(ExtractedImage.created_at.asc())
            images = db.scalars(stmt).all()
            if not images and page is not None:
                # Fallback: check if document has general images (e.g. DOCX or unpaged)
                fallback_stmt = (
                    select(ExtractedImage)
                    .join(SourceVersion, ExtractedImage.source_version_id == SourceVersion.id)
                    .where(
                        ExtractedImage.dataset_id == dataset_id,
                        SourceVersion.source_id == source_id,
                        SourceVersion.version_number == version_number,
                        ExtractedImage.page_number.is_(None),
                    )
                )
                images = db.scalars(fallback_stmt).all()

            results = []
            for img in images:
                results.append({
                    "image_id": str(img.id),
                    "storage_path": img.storage_path,
                    "mime_type": img.mime_type,
                    "caption": img.caption,
                    "page_number": img.page_number,
                    "dataset_id": str(img.dataset_id),
                    "source_id": str(source_id),
                    "api_url": f"/api/v1/datasets/{img.dataset_id}/sources/{source_id}/images/{img.id}",
                })
            return results

        lookup = _db_lookup

    enriched_chunks: list[EvidenceChunk] = []
    seen_image_ids: set[str] = set()
    total_images_collected = 0

    for chunk in chunks:
        loc = chunk.locator
        matched_images: list[dict] = []
        if lookup:
            raw_imgs = lookup(chunk.dataset_id, loc.source_id, loc.source_version, loc.page)
            for img in raw_imgs:
                img_id = img.get("image_id")
                matched_images.append(img)
                if img_id and img_id not in seen_image_ids:
                    seen_image_ids.add(img_id)
                    total_images_collected += 1
                if len(matched_images) >= max_images_per_chunk:
                    break

        enriched_chunk = EvidenceChunk(
            dataset_id=chunk.dataset_id,
            locator=chunk.locator,
            text=chunk.text,
            images=tuple(matched_images),
        )
        enriched_chunks.append(enriched_chunk)

    return enriched_chunks


def extract_representative_images(
    chunks: Sequence[EvidenceChunk],
    max_images: int = 3,
) -> list[dict]:
    """Lấy danh sách tối đa 2-3 ảnh tiêu biểu nhất từ các chunks đã xếp hạng,
    ưu tiên ảnh của các chunk có độ tương đồng cao nhất xếp trước.
    """
    seen_ids = set()
    representative: list[dict] = []
    for chunk in chunks:
        for img in getattr(chunk, "images", ()):
            img_id = img.get("image_id")
            if img_id and img_id not in seen_ids:
                seen_ids.add(img_id)
                representative.append(img)
                if len(representative) >= max_images:
                    return representative
    return representative


def retrieve_grounded_chunks(
    chunks: Sequence[EvidenceChunk],
    db: Any = None,
    max_images: int = 3,
) -> tuple[list[EvidenceChunk], list[dict]]:
    """Làm giàu chunks với ảnh trích xuất và chọn top ảnh đại diện."""
    enriched = enrich_chunks_with_images(chunks, db=db, max_total_images=max_images)
    top_images = extract_representative_images(enriched, max_images=max_images)
    return enriched, top_images


def fuse_hybrid_chunks(
    lexical_chunks: Sequence[EvidenceChunk],
    dense_chunks: Sequence[EvidenceChunk],
    top_k: int = 5,
) -> list[EvidenceChunk]:
    """Kết hợp kết quả từ nhánh tìm kiếm chính xác (Lexical Exact Match)
    và nhánh tìm kiếm ngữ nghĩa (Dense Vector Cosine Similarity).

    Quy tắc xếp hạng (per RAG-02):
    1. Các đoạn bằng chứng khớp mã định danh chính xác (DH001, ERR-502) luôn được ưu tiên xếp đầu tiên.
    2. Điền tiếp các đoạn tương đồng ngữ nghĩa dense vector có điểm số cao nhất.
    3. Khử trùng lặp dựa trên (source_id, locator, text).
    4. Giới hạn tối đa top_k kết quả.
    """
    seen_keys = set()
    fused: list[EvidenceChunk] = []

    # 1. Thêm kết quả lexical trước
    for chunk in lexical_chunks:
        loc = chunk.locator
        key = (loc.source_id, loc.page, loc.row, loc.line_start, loc.json_path, chunk.text[:100])
        if key not in seen_keys:
            seen_keys.add(key)
            fused.append(chunk)
            if len(fused) >= top_k:
                return fused

    # 2. Thêm kết quả dense vector
    for chunk in dense_chunks:
        loc = chunk.locator
        key = (loc.source_id, loc.page, loc.row, loc.line_start, loc.json_path, chunk.text[:100])
        if key not in seen_keys:
            seen_keys.add(key)
            fused.append(chunk)
            if len(fused) >= top_k:
                return fused

    return fused


class HybridRetriever:
    """Động cơ kết hợp tìm kiếm chính xác và ngữ nghĩa vector (RAG-02)."""

    def __init__(self, embedding_provider: EmbeddingProvider, lexical_matcher: LexicalMatcher | None = None):
        self.embedding_provider = embedding_provider
        self.lexical_matcher = lexical_matcher or LexicalMatcher()

    def fuse(
        self,
        lexical_chunks: Sequence[EvidenceChunk],
        dense_chunks: Sequence[EvidenceChunk],
        top_k: int = 5,
    ) -> list[EvidenceChunk]:
        return fuse_hybrid_chunks(lexical_chunks, dense_chunks, top_k=top_k)


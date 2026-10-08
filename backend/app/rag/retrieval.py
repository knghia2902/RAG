from typing import Sequence
from app.rag.contracts import EmbeddingProvider, EvidenceChunk, RetrievalRequest, Retriever
from app.rag.lexical import LexicalMatcher


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

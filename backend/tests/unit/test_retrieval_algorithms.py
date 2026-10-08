from uuid import uuid4
import pytest
from app.rag.contracts import EvidenceChunk, SourceLocator
from app.rag.filters import ScopeCriteria, ScopeFilterBuilder
from app.rag.lexical import extract_identifiers, is_exact_match, LexicalMatcher
from app.rag.retrieval import fuse_hybrid_chunks


def test_extract_identifiers():
    query = "Kiểm tra mã đơn DH001 và lỗi ERR-502 trên luồng xử lý TRK-8829"
    matcher = LexicalMatcher()
    identifiers = matcher.extract_identifiers(query)
    assert "DH001" in identifiers
    assert "ERR-502" in identifiers
    assert "TRK-8829" in identifiers


def test_lexical_exact_match_disambiguation():
    # RAG-02: DH001 must NEVER match DH010 or DH0010
    matcher = LexicalMatcher()
    assert matcher.is_exact_match("Đơn hàng DH001 bị lỗi tại kho A", "DH001") is True
    assert matcher.is_exact_match("Đơn hàng (DH001) đã xuất kho", "DH001") is True
    assert matcher.is_exact_match("Đơn hàng [DH001] đang chờ", "DH001") is True
    assert matcher.is_exact_match("Mã đơn: DH001.", "DH001") is True

    # Negative matches
    assert matcher.is_exact_match("Đơn hàng DH010 giao thành công", "DH001") is False
    assert matcher.is_exact_match("Đơn hàng DH0010 bị trễ", "DH001") is False
    assert matcher.is_exact_match("Đơn hàng XDH001 đã huỷ", "DH001") is False
    assert matcher.is_exact_match("Không có mã nào ở đây", "DH001") is False


def test_scope_criteria_and_filter_builder():
    ds_a = uuid4()
    ds_b = uuid4()
    ds_c = uuid4()

    # Case 1: no target -> effective is all allowed
    crit1 = ScopeFilterBuilder.build_filters(allowed_dataset_ids={ds_a, ds_b})
    assert crit1.effective_dataset_ids == {ds_a, ds_b}

    # Case 2: valid subset
    crit2 = ScopeFilterBuilder.build_filters(
        allowed_dataset_ids={ds_a, ds_b},
        target_dataset_ids={ds_a},
    )
    assert crit2.effective_dataset_ids == {ds_a}

    # Case 3: unauthorized target -> raises PermissionError
    with pytest.raises(PermissionError) as exc_info:
        ScopeFilterBuilder.build_filters(
            allowed_dataset_ids={ds_a},
            target_dataset_ids={ds_c},
        )
    assert "Không có quyền truy cập" in str(exc_info.value)


def test_fuse_hybrid_chunks_prioritization_and_dedup():
    src_id = uuid4()
    ds_id = uuid4()

    loc1 = SourceLocator(source_id=src_id, source_version=1, line_start=1, line_end=5)
    loc2 = SourceLocator(source_id=src_id, source_version=1, line_start=6, line_end=10)
    loc3 = SourceLocator(source_id=src_id, source_version=1, line_start=11, line_end=15)

    lexical_chunk1 = EvidenceChunk(
        dataset_id=ds_id,
        locator=loc1,
        text="Thông tin chính xác mã DH001 tại trạm phân loại.",
    )

    dense_chunk1 = EvidenceChunk(
        dataset_id=ds_id,
        locator=loc1,  # Duplicate of lexical_chunk1
        text="Thông tin chính xác mã DH001 tại trạm phân loại.",
    )
    dense_chunk2 = EvidenceChunk(
        dataset_id=ds_id,
        locator=loc2,
        text="Quy trình xử lý sự cố kẹt băng tải hàng hóa.",
    )
    dense_chunk3 = EvidenceChunk(
        dataset_id=ds_id,
        locator=loc3,
        text="Hướng dẫn bảo trì định kỳ cảm biến quang.",
    )

    fused = fuse_hybrid_chunks(
        lexical_chunks=[lexical_chunk1],
        dense_chunks=[dense_chunk1, dense_chunk2, dense_chunk3],
        top_k=2,
    )

    # 1. Lexical chunk should be ranked first
    assert len(fused) == 2
    assert fused[0].text == lexical_chunk1.text

    # 2. Duplicate dense_chunk1 should be skipped, so dense_chunk2 is next
    assert fused[1].text == dense_chunk2.text

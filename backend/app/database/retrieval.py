from datetime import datetime
from uuid import UUID
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.database.models import CanonicalRecord, EmbeddingRecord, Source, SourceVersion
from app.rag.contracts import EvidenceChunk, SourceLocator
from app.rag.filters import ScopeCriteria
from app.rag.lexical import extract_identifiers, is_exact_match
from app.rag.retrieval import fuse_hybrid_chunks


def _record_to_evidence(record: CanonicalRecord, source: Source, version: SourceVersion) -> EvidenceChunk:
    loc_data = dict(record.locator_data or {})
    # Build clean SourceLocator
    locator = SourceLocator(
        source_id=source.id,
        source_version=version.version_number,
        page=loc_data.get("page"),
        section=loc_data.get("section"),
        sheet=loc_data.get("sheet"),
        row=loc_data.get("row"),
        event=loc_data.get("event"),
        record=loc_data.get("record"),
        line_start=loc_data.get("line_start"),
        line_end=loc_data.get("line_end"),
        json_path=loc_data.get("json_path"),
    )
    return EvidenceChunk(
        dataset_id=record.dataset_id,
        locator=locator,
        text=record.content_text,
    )


def search_lexical_records(
    db: Session,
    identifiers: list[str],
    dataset_ids: set[UUID],
    profile_id: str | None = None,
) -> list[EvidenceChunk]:
    """Tìm kiếm chính xác các bản ghi chứa đúng mã định danh (RAG-02)."""
    if not identifiers or not dataset_ids:
        return []

    # Xây dựng các điều kiện regex hoặc exact match
    regex_clauses = [
        CanonicalRecord.content_text.op("~*")(rf"\m{ident}\M")
        for ident in identifiers
    ]

    stmt = (
        select(CanonicalRecord, Source, SourceVersion)
        .join(SourceVersion, CanonicalRecord.source_version_id == SourceVersion.id)
        .join(Source, SourceVersion.source_id == Source.id)
        .where(
            CanonicalRecord.dataset_id.in_(dataset_ids),
            Source.deleted_at.is_(None),
            Source.active_version_id == SourceVersion.id,
            or_(*regex_clauses),
        )
    )
    if profile_id:
        stmt = stmt.where(Source.profile_id == profile_id)

    stmt = stmt.order_by(CanonicalRecord.position).limit(20)
    rows = db.execute(stmt).all()

    # Thẩm định lại bằng Python để tuyệt đối không có false positive (ví dụ DH001 vs DH010)
    results: list[EvidenceChunk] = []
    for record, source, version in rows:
        if any(is_exact_match(record.content_text, ident) for ident in identifiers):
            results.append(_record_to_evidence(record, source, version))

    return results


def search_dense_records(
    db: Session,
    query_vector: list[float],
    dataset_ids: set[UUID],
    top_k: int = 10,
    profile_id: str | None = None,
    start_time: datetime | None = None,
    end_time: datetime | None = None,
) -> list[EvidenceChunk]:
    """Tìm kiếm ngữ nghĩa dense vector cosine similarity trong PostgreSQL pgvector."""
    if not dataset_ids or not query_vector:
        return []

    distance_expr = EmbeddingRecord.embedding.cosine_distance(query_vector).label("distance")
    stmt = (
        select(CanonicalRecord, Source, SourceVersion, distance_expr)
        .join(EmbeddingRecord, EmbeddingRecord.canonical_record_id == CanonicalRecord.id)
        .join(SourceVersion, CanonicalRecord.source_version_id == SourceVersion.id)
        .join(Source, SourceVersion.source_id == Source.id)
        .where(
            EmbeddingRecord.dataset_id.in_(dataset_ids),
            Source.deleted_at.is_(None),
            Source.active_version_id == SourceVersion.id,
        )
    )

    if profile_id:
        stmt = stmt.where(Source.profile_id == profile_id)
    if start_time:
        stmt = stmt.where(CanonicalRecord.created_at >= start_time)
    if end_time:
        stmt = stmt.where(CanonicalRecord.created_at <= end_time)

    stmt = stmt.order_by("distance").limit(top_k)
    rows = db.execute(stmt).all()

    return [_record_to_evidence(rec, src, ver) for rec, src, ver, _ in rows]


def execute_hybrid_retrieval(
    db: Session,
    query: str,
    query_vector: list[float],
    scope_criteria: ScopeCriteria,
    top_k: int = 5,
) -> list[EvidenceChunk]:
    """Thực thi toàn bộ luồng Hybrid Retrieval kết hợp Lexical và Dense."""
    effective_datasets = scope_criteria.effective_dataset_ids

    # 1. Nhánh Lexical Match
    identifiers = extract_identifiers(query)
    lexical_chunks = (
        search_lexical_records(
            db=db,
            identifiers=identifiers,
            dataset_ids=effective_datasets,
            profile_id=scope_criteria.profile_id,
        )
        if identifiers
        else []
    )

    # 2. Nhánh Dense Vector
    dense_chunks = search_dense_records(
        db=db,
        query_vector=query_vector,
        dataset_ids=effective_datasets,
        top_k=top_k * 2,
        profile_id=scope_criteria.profile_id,
        start_time=scope_criteria.start_time,
        end_time=scope_criteria.end_time,
    )

    # 3. Kết hợp và xếp hạng
    return fuse_hybrid_chunks(
        lexical_chunks=lexical_chunks,
        dense_chunks=dense_chunks,
        top_k=top_k,
    )

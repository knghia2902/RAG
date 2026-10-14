from typing import Optional
from sqlalchemy.orm import Session

from app.database.retrieval import search_dense_records
from app.rag.contracts import AuthorizedScope, EmbeddingProvider, EvidenceChunk
from app.rag.retrieval import HybridRetriever
from app.modules.log_analysis.contracts import CategorizedEvidenceChunk, EvidenceKindEnum


class SOPMatcher:
    """Vector-based retrieval matching relevant SOP standard procedures and similar historical incidents."""

    def __init__(
        self,
        retriever: Optional[HybridRetriever] = None,
        embedding_provider: Optional[EmbeddingProvider] = None,
        db: Optional[Session] = None,
    ):
        self.retriever = retriever
        self.embedding_provider = embedding_provider or (retriever.embedding_provider if retriever else None)
        self.db = db

    def match_sop_and_precedents(
        self,
        error_description: str,
        authorized_scope: AuthorizedScope,
        db: Optional[Session] = None,
        top_k: int = 5,
    ) -> list[EvidenceChunk]:
        """Search vector database for relevant SOP standard procedures and historical incident precedents.

        Args:
            error_description: Error summary or query to match against procedures and past incidents.
            authorized_scope: Current authorized dataset boundaries.
            db: Optional database session (falls back to self.db).
            top_k: Max chunks per category.

        Returns:
            List of EvidenceChunk (specifically CategorizedEvidenceChunk) with evidence_kind attribute.
        """
        active_db = db or self.db
        if not active_db or not self.embedding_provider or not error_description.strip():
            return []

        dataset_ids = set(authorized_scope.dataset_ids)
        if not dataset_ids:
            return []

        if hasattr(self.embedding_provider, "embed_query"):
            query_vector = list(self.embedding_provider.embed_query(error_description))
        else:
            query_vector = list(self.embedding_provider.embed((error_description,))[0])


        # 1. Retrieve SOP procedures
        sop_raw = search_dense_records(
            db=active_db,
            query_vector=query_vector,
            dataset_ids=dataset_ids,
            top_k=top_k,
            profile_id="sop",
        )
        sop_chunks: list[EvidenceChunk] = [
            CategorizedEvidenceChunk(
                dataset_id=c.dataset_id,
                locator=c.locator,
                text=c.text,
                evidence_kind=EvidenceKindEnum.SOP_PROCEDURE,
            )
            for c in sop_raw
        ]

        # 2. Retrieve precedent incidents
        precedent_raw = search_dense_records(
            db=active_db,
            query_vector=query_vector,
            dataset_ids=dataset_ids,
            top_k=top_k,
            profile_id="incident",
        )
        precedent_chunks: list[EvidenceChunk] = [
            CategorizedEvidenceChunk(
                dataset_id=c.dataset_id,
                locator=c.locator,
                text=c.text,
                evidence_kind=EvidenceKindEnum.PRECEDENT_INCIDENT,
            )
            for c in precedent_raw
        ]

        # If profile="incident" returned nothing, also check "ticket"
        if not precedent_chunks:
            ticket_raw = search_dense_records(
                db=active_db,
                query_vector=query_vector,
                dataset_ids=dataset_ids,
                top_k=top_k,
                profile_id="ticket",
            )
            precedent_chunks = [
                CategorizedEvidenceChunk(
                    dataset_id=c.dataset_id,
                    locator=c.locator,
                    text=c.text,
                    evidence_kind=EvidenceKindEnum.PRECEDENT_INCIDENT,
                )
                for c in ticket_raw
            ]

        return sop_chunks + precedent_chunks

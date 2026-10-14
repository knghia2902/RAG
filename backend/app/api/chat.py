from datetime import datetime
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies import get_account
from app.api.schemas import (
    ChatMessageDTO,
    ChatQueryRequestDTO,
    ChatQueryResponseDTO,
    ChatSessionDTO,
    CitationPreviewResponseDTO,
    SourceLocatorDTO,
)
from app.auth.policy import allowed_dataset_ids, current_account
from app.database.datasets import recheck_response
from app.database.models import (
    Account,
    CanonicalRecord,
    ChatMessage,
    ChatSession,
    Dataset,
    Source,
    SourceVersion,
    utcnow,
)
from app.database.retrieval import execute_hybrid_retrieval
from app.database.session import get_db
from app.llm.generation import GroundedGenerator
from app.providers import get_embedding_provider, get_llm_provider
from app.rag.filters import ScopeCriteria

router = APIRouter(prefix="/api/v1/chat", tags=["chat"])


@router.get("/sessions", response_model=list[ChatSessionDTO])
def list_sessions(
    account: Account = Depends(get_account),
    db: Session = Depends(get_db),
):
    """Lấy danh sách các phiên trò chuyện của người dùng hiện tại."""
    account = current_account(db, account)
    sessions = db.scalars(
        select(ChatSession)
        .where(ChatSession.account_id == account.id)
        .order_by(ChatSession.updated_at.desc())
    ).all()
    return [ChatSessionDTO.model_validate(s) for s in sessions]


@router.post("/sessions", response_model=ChatSessionDTO, status_code=201)
def create_session(
    account: Account = Depends(get_account),
    db: Session = Depends(get_db),
):
    """Tạo một phiên hỏi đáp mới."""
    account = current_account(db, account)
    session = ChatSession(
        account_id=account.id,
        title="Cuộc trò chuyện mới",
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return ChatSessionDTO.model_validate(session)


@router.delete("/sessions/{session_id}")
def delete_session(
    session_id: UUID,
    account: Account = Depends(get_account),
    db: Session = Depends(get_db),
):
    """Xóa phiên hỏi đáp và các tin nhắn liên quan (T-03-11: chỉ cho phép chủ sở hữu)."""
    account = current_account(db, account)
    session = db.scalar(
        select(ChatSession).where(
            ChatSession.id == session_id,
            ChatSession.account_id == account.id,
        )
    )
    if not session:
        raise HTTPException(404, "Không tìm thấy cuộc trò chuyện.")

    db.delete(session)
    db.commit()
    return {"ok": True}


@router.get("/sessions/{session_id}/messages", response_model=list[ChatMessageDTO])
def list_session_messages(
    session_id: UUID,
    account: Account = Depends(get_account),
    db: Session = Depends(get_db),
):
    """Lấy lịch sử tin nhắn của phiên chat, tự động loại bỏ citation của các dataset đã mất quyền (D-05)."""
    account = current_account(db, account)
    session = db.scalar(
        select(ChatSession).where(
            ChatSession.id == session_id,
            ChatSession.account_id == account.id,
        )
    )
    if not session:
        raise HTTPException(404, "Không tìm thấy cuộc trò chuyện.")

    messages = db.scalars(
        select(ChatMessage)
        .where(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at.asc())
    ).all()

    allowed = allowed_dataset_ids(db, account)
    sanitized_messages = []
    for msg in messages:
        # Lọc citations theo quyền hiện tại
        active_citations = []
        for cit in msg.citations or []:
            try:
                ds_id = UUID(cit.get("dataset_id", ""))
                if ds_id in allowed:
                    active_citations.append(cit)
            except (ValueError, TypeError):
                continue

        sanitized_messages.append(
            ChatMessageDTO(
                id=msg.id,
                role=msg.role,
                content=msg.content,
                citations=active_citations,
                has_uncertainty=msg.has_uncertainty,
                has_conflict=msg.has_conflict,
                created_at=msg.created_at,
            )
        )

    return sanitized_messages


@router.post("/query", response_model=ChatQueryResponseDTO)
def execute_query(
    payload: ChatQueryRequestDTO,
    account: Account = Depends(get_account),
    db: Session = Depends(get_db),
):
    """Thực thi câu hỏi tiếng Việt, truy xuất tri thức lai và sinh câu trả lời có trích dẫn."""
    account = current_account(db, account)

    # 1. Xác định hoặc tạo mới session
    session = None
    if payload.session_id:
        session = db.scalar(
            select(ChatSession).where(
                ChatSession.id == payload.session_id,
                ChatSession.account_id == account.id,
            )
        )
        if not session:
            raise HTTPException(404, "Không tìm thấy phiên trò chuyện.")
    else:
        title = payload.question[:40].strip() + ("..." if len(payload.question) > 40 else "")
        session = ChatSession(
            account_id=account.id,
            title=title,
        )
        db.add(session)
        db.flush()

    # 2. Tính toán quyền Dataset (AUTH-04)
    allowed_all = allowed_dataset_ids(db, account)
    if payload.dataset_ids:
        target_set = set(payload.dataset_ids)
        effective_datasets = allowed_all & target_set
        if not effective_datasets:
            raise HTTPException(403, "Không có quyền truy cập vào bất kỳ Dataset nào trong phạm vi yêu cầu.")
    else:
        effective_datasets = allowed_all

    # 3. Thực hiện truy xuất tri thức nếu có quyền
    citations_data = []
    if not effective_datasets:
        answer_text = "Không tìm thấy thông tin xác thực từ các nguồn dữ liệu được cấp quyền. Tài khoản của bạn hiện chưa được cấp quyền truy cập vào Dataset nào."
        has_uncertainty = True
        has_conflict = False
    else:
        emb_provider = get_embedding_provider()
        query_vec = emb_provider.embed((payload.question,))[0]

        criteria = ScopeCriteria(
            allowed_dataset_ids=effective_datasets,
            profile_id=payload.profile_id,
            start_time=payload.start_time,
            end_time=payload.end_time,
        )

        evidence_chunks = execute_hybrid_retrieval(
            db=db,
            query=payload.question,
            query_vector=list(query_vec),
            scope_criteria=criteria,
            top_k=5,
        )

        llm_provider = get_llm_provider()
        generator = GroundedGenerator(llm_provider=llm_provider)
        grounded_result = generator.generate_answer(
            question=payload.question,
            evidence=evidence_chunks,
        )

        answer_text = grounded_result.answer_text
        has_uncertainty = grounded_result.has_uncertainty
        has_conflict = grounded_result.has_conflict

        for cit in grounded_result.citations:
            citations_data.append({
                "citation_index": cit.citation_index,
                "dataset_id": str(cit.dataset_id),
                "source_id": str(cit.source_id),
                "source_version": cit.source_version,
                "locator": cit.locator.model_dump(mode="json"),
                "excerpt_text": cit.excerpt_text,
            })

    # 4. Lưu tin nhắn người dùng và tin nhắn phản hồi
    user_msg = ChatMessage(
        session_id=session.id,
        role="user",
        content=payload.question,
        citations=[],
        has_uncertainty=False,
        has_conflict=False,
    )
    asst_msg = ChatMessage(
        session_id=session.id,
        role="assistant",
        content=answer_text,
        citations=citations_data,
        has_uncertainty=has_uncertainty,
        has_conflict=has_conflict,
    )
    session.updated_at = utcnow()
    db.add_all([user_msg, asst_msg])
    db.commit()
    db.refresh(asst_msg)

    message_dto = ChatMessageDTO(
        id=asst_msg.id,
        role=asst_msg.role,
        content=asst_msg.content,
        citations=citations_data,
        has_uncertainty=asst_msg.has_uncertainty,
        has_conflict=asst_msg.has_conflict,
        created_at=asst_msg.created_at,
    )

    return ChatQueryResponseDTO(
        session_id=session.id,
        message=message_dto,
        citations=citations_data,
    )


@router.get("/citations/preview", response_model=CitationPreviewResponseDTO)
def preview_citation(
    dataset_id: UUID = Query(...),
    source_id: UUID = Query(...),
    citation_index: int = Query(1, ge=1),
    account: Account = Depends(get_account),
    db: Session = Depends(get_db),
):
    """Xem trước chi tiết bằng chứng trích dẫn kèm kiểm tra quyền Live Scope Recheck (D-05, RAG-04)."""
    account = current_account(db, account)

    # 1. Live Scope Recheck: nếu quyền dataset bị thu hồi -> chặn ngay lập tức với 403
    allowed = allowed_dataset_ids(db, account)
    if dataset_id not in allowed:
        raise HTTPException(403, "Quyền truy cập nguồn dữ liệu đã thay đổi hoặc bị thu hồi.")
    recheck_response(db, account, {dataset_id})

    # 2. Lấy thông tin Dataset và Source
    dataset = db.get(Dataset, dataset_id)
    dataset_name = dataset.name if dataset else "Dataset"

    source = db.get(Source, source_id)
    if not source or source.deleted_at is not None:
        raise HTTPException(404, "Nguồn dữ liệu không tồn tại hoặc đã bị xóa.")

    version = db.get(SourceVersion, source.active_version_id)
    version_num = version.version_number if version else 1

    # 3. Lấy bản ghi canonical record đầu tiên của active version
    rec = db.scalars(
        select(CanonicalRecord)
        .where(CanonicalRecord.source_version_id == source.active_version_id)
        .order_by(CanonicalRecord.position.asc())
        .limit(1)
    ).first()

    if rec:
        loc_data = dict(rec.locator_data or {})
        excerpt = rec.content_text
        locator = SourceLocatorDTO(
            source_id=source.id,
            source_version=version_num,
            page=loc_data.get("page"),
            section=loc_data.get("section"),
            sheet=loc_data.get("sheet"),
            row=loc_data.get("row"),
            line_start=loc_data.get("line_start"),
            line_end=loc_data.get("line_end"),
            json_path=loc_data.get("json_path"),
        )
    else:
        excerpt = "Không có đoạn trích khả dụng."
        locator = SourceLocatorDTO(
            source_id=source.id,
            source_version=version_num,
        )

    return CitationPreviewResponseDTO(
        citation_index=citation_index,
        dataset_id=dataset_id,
        dataset_name=dataset_name,
        source_id=source_id,
        logical_filename=source.logical_filename,
        version_number=version_num,
        locator=locator,
        excerpt_text=excerpt,
    )

from uuid import uuid4
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies import get_account
from app.api.schemas import ModelConfigDTO, UpdateModelConfigDTO
from app.auth.policy import current_account, require_admin
from app.config import get_settings
from app.database.models import Account, EmbeddingRecord
from app.database.session import get_db

router = APIRouter(prefix="/api/v1/config", tags=["configuration"])

# Dynamic runtime model override cache
_RUNTIME_MODEL_CONFIG = {
    "llm_model": "gpt-4o-mini",
    "embedding_model": "text-embedding-3-small",
}


@router.get("/models", response_model=ModelConfigDTO)
def get_model_config(
    account: Account = Depends(get_account),
    db: Session = Depends(get_db),
):
    """Lấy thông tin cấu hình model và trạng thái index (chỉ dành cho Admin).
    Bảo đảm SYS-02: không để lộ raw API key ra giao diện Web.
    """
    account = current_account(db, account)
    require_admin(account)

    settings = get_settings()
    has_openai = bool(settings.openai_api_key.get_secret_value()) if settings.openai_api_key else False
    has_gemini = bool(settings.gemini_api_key.get_secret_value()) if settings.gemini_api_key else False

    # Tìm index version gần nhất từ database nếu có, ngược lại dùng version mặc định
    latest_index_version = db.scalar(
        select(EmbeddingRecord.index_version)
        .order_by(EmbeddingRecord.created_at.desc())
        .limit(1)
    )
    index_ver_str = str(latest_index_version) if latest_index_version else "00000000-0000-0000-0000-000000000001"

    if settings.test_mode:
        llm_prov = "fake"
        llm_mod = _RUNTIME_MODEL_CONFIG["llm_model"]
    elif settings.llm_provider == "gemini" or (has_gemini and settings.llm_provider != "openai"):
        llm_prov = "gemini" if has_gemini else "fake"
        llm_mod = _RUNTIME_MODEL_CONFIG["llm_model"] if _RUNTIME_MODEL_CONFIG["llm_model"] != "gpt-4o-mini" else "gemini-flash-lite-latest"
    elif has_openai:
        llm_prov = "openai"
        llm_mod = _RUNTIME_MODEL_CONFIG["llm_model"]
    else:
        llm_prov = "fake"
        llm_mod = _RUNTIME_MODEL_CONFIG["llm_model"]

    embedding_provider = "fake" if (settings.test_mode or not has_openai) else "openai"

    return ModelConfigDTO(
        embedding_provider=embedding_provider,
        embedding_model=_RUNTIME_MODEL_CONFIG["embedding_model"],
        embedding_dimension=1536,
        index_version=index_ver_str,
        llm_provider=llm_prov,
        llm_model=llm_mod,
        openai_configured=has_openai,
        gemini_configured=has_gemini,
    )


@router.post("/models", response_model=ModelConfigDTO)
def update_model_config(
    payload: UpdateModelConfigDTO,
    account: Account = Depends(get_account),
    db: Session = Depends(get_db),
):
    """Cập nhật cấu hình mô hình runtime (Admin only)."""
    account = current_account(db, account)
    require_admin(account)

    if payload.llm_model:
        _RUNTIME_MODEL_CONFIG["llm_model"] = payload.llm_model
    if payload.embedding_model:
        _RUNTIME_MODEL_CONFIG["embedding_model"] = payload.embedding_model

    return get_model_config(account=account, db=db)

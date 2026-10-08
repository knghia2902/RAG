# Phase 03: Grounded Knowledge Retrieval - Pattern Map

**Mapped:** 2026-10-08  
**Files analyzed:** 14  
**Analogs found:** 14 / 14  

---

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|---|---|---|---|---|
| `backend/app/providers/openai_embedding.py` | provider / adapter | request-response (external API) | `backend/app/rag/parsers/docling_adapter.py` | role-match |
| `backend/app/providers/openai_llm.py` | provider / adapter | request-response (external API) | `backend/app/rag/parsers/docling_adapter.py` | role-match |
| `backend/app/providers/fake.py` | test mock / provider | in-memory transform | `backend/tests/support.py` | exact |
| `backend/app/database/models.py` (add ChatSession, ChatMessage, EmbeddingRecord) | model | CRUD / ORM persistence | `backend/app/database/models.py` (Source, CanonicalRecord) | exact |
| `backend/app/rag/retrieval.py` | service | hybrid retrieval / transform | `backend/app/rag/parsers/structured.py` | role-match |
| `backend/app/llm/secret_masking.py` | utility / security | text regex masking | `backend/app/auth/passwords.py` | role-match |
| `backend/app/llm/generation.py` | service | prompt assembly + LLM call | `backend/app/rag/parsers/profiles.py` | role-match |
| `backend/app/api/chat.py` | route controller | request-response | `backend/app/api/sources.py` | exact |
| `backend/app/api/config.py` | route controller | request-response | `backend/app/api/status.py` | exact |
| `frontend/src/app/(workspace)/chat/page.tsx` | page component | interactive state / API fetch | `frontend/src/app/(workspace)/datasets/page.tsx` | exact |
| `frontend/src/components/EvidencePreview.tsx` | component / drawer | interactive preview | `frontend/src/app/(workspace)/datasets/page.tsx` (excerpt preview modal) | exact |
| `frontend/src/components/Sidebar.tsx` | navigation component | layout / link rendering | `frontend/src/components/Sidebar.tsx` | exact |
| `backend/tests/integration/test_chat_rag.py` | test | integration / API verification | `backend/tests/integration/test_sources.py` | exact |
| `backend/tests/unit/test_secret_masking.py` | test | unit verification | `backend/tests/unit/test_module_boundaries.py` | exact |

---

## Pattern Assignments

### 1. `backend/app/providers/openai_embedding.py` & `openai_llm.py` (Provider Adapters)

**Analog:** `backend/app/rag/parsers/docling_adapter.py` and `backend/app/rag/contracts.py`

**Crucial Architectural Rule (`test_module_boundaries.py`):**
- Third-party packages `openai`, `langchain`, `langchain_openai`, etc. MUST ONLY be imported inside `backend/app/providers/`.
- Core packages (`app.rag`, `app.llm`, `app.database`, `app.auth`) must NEVER import `openai` or `langchain`.

**Interface Protocol Pattern:**
```python
# Defined in app.rag.contracts:
class EmbeddingProvider(Protocol):
    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        ...

# Defined in app.llm.contracts:
class LLMProvider(Protocol):
    def generate(self, request: GenerationRequest) -> GenerationResult:
        ...
```

**Provider Implementation Pattern:**
```python
from app.rag.contracts import EmbeddingProvider, EmbeddingIndex
from app.llm.contracts import LLMProvider, GenerationRequest, GenerationResult

class OpenAIEmbeddingAdapter:
    def __init__(self, api_key: str, model: str = "text-embedding-3-small", dimension: int = 1536):
        self.api_key = api_key
        self.model = model
        self.dimension = dimension

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        # Calls OpenAI SDK embeddings.create
        ...

class OpenAILLMAdapter:
    def __init__(self, api_key: str, model: str = "gpt-4o-mini", timeout: float = 30.0):
        self.api_key = api_key
        self.model = model
        self.timeout = timeout

    def generate(self, request: GenerationRequest) -> GenerationResult:
        # Calls OpenAI SDK chat.completions.create with token budgeting and timeout handling
        ...
```

---

### 2. `backend/app/database/models.py` (Chat Sessions, Messages, and Vector Embeddings)

**Analog:** `backend/app/database/models.py` (`CanonicalRecord`, `Source`)

**Core SQLAlchemy Pattern:**
```python
from datetime import datetime, timezone
import uuid
from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column
from pgvector.sqlalchemy import Vector
from app.database.models import Base, utcnow

class ChatSession(Base):
    __tablename__ = "chat_sessions"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("accounts.id"), index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

class ChatMessage(Base):
    __tablename__ = "chat_messages"
    __table_args__ = (
        CheckConstraint("role IN ('user', 'assistant')", name="chat_message_role_valid"),
    )
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("chat_sessions.id", ondelete="CASCADE"), index=True, nullable=False)
    role: Mapped[str] = mapped_column(String(16), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    citations: Mapped[list[dict]] = mapped_column(JSONB, default=list, nullable=False) # list of {citation_num, record_id, locator}
    has_uncertainty: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    has_conflict: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

class EmbeddingRecord(Base):
    __tablename__ = "embedding_records"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    canonical_record_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("canonical_records.id", ondelete="CASCADE"), index=True, nullable=False)
    dataset_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("datasets.id"), index=True, nullable=False)
    source_version_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("source_versions.id"), index=True, nullable=False)
    model_name: Mapped[str] = mapped_column(String(128), nullable=False)
    dimension: Mapped[int] = mapped_column(Integer, nullable=False)
    index_version: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    embedding = mapped_column(Vector(1536), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
```

---

### 3. `backend/app/api/chat.py` (Chat Controller & Live Scope Recheck)

**Analog:** `backend/app/api/sources.py` (lines 42-53)

**Auth, ACL Scope & Live Recheck Pattern:**
```python
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.api.dependencies import get_account
from app.auth.policy import allowed_dataset_ids, current_account
from app.database.datasets import recheck_response
from app.database.session import get_db

router = APIRouter(prefix="/api/v1/chat", tags=["chat"])

@router.get("/sessions")
def list_sessions(
    account: Account = Depends(get_account),
    db: Session = Depends(get_db),
):
    account = current_account(db, account)
    # Return user's chat sessions ordered by updated_at desc
    ...

@router.post("/query")
def submit_query(
    request: ChatQueryRequestDTO,
    account: Account = Depends(get_account),
    db: Session = Depends(get_db),
):
    account = current_account(db, account)
    scope = allowed_dataset_ids(db, account)
    # Filter requested datasets by authorized scope
    effective_datasets = scope if not request.dataset_ids else (set(request.dataset_ids) & scope)
    if not effective_datasets:
        raise HTTPException(403, "Không có quyền truy cập vào dataset nào được yêu cầu.")
    
    # Live scope recheck right before execution
    recheck_response(db, account, effective_datasets)
    ...
```

---

### 4. `backend/app/llm/secret_masking.py` (SYS-03 Secret Masking Egress Filter)

**Analog:** Regular expression matching and token normalization pattern

**Egress Masking Pattern:**
```python
import re

PATTERNS = [
    (re.compile(r"(?i)(api[_-]?key|secret|token|password|bearer|authorization)\s*[:=]\s*['\"]?([a-zA-Z0-9_\-\.]{8,})['\"]?"), r"\1=[REDACTED]"),
    (re.compile(r"sk-[a-zA-Z0-9]{20,T}"), "sk-[REDACTED]"),
    (re.compile(r"(ghp|gho|ghu|ghs|ghr)_[a-zA-Z0-9]{36}"), "[REDACTED_GITHUB_TOKEN]"),
    (re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+"), "[REDACTED_EMAIL]"), # if sensitive
]

def mask_secrets(text: str) -> str:
    masked = text
    for pattern, replacement in PATTERNS:
        masked = pattern.sub(replacement, masked)
    return masked
```

---

### 5. `frontend/src/app/(workspace)/chat/page.tsx` (Two-Column Chat UI)

**Analog:** `frontend/src/app/(workspace)/datasets/page.tsx`

**State Management & Accessibility Pattern:**
```typescript
"use client";
import { useState, useEffect, useRef } from "react";
import { api } from "@/lib/api";
import { useWorkspaceSession } from "../layout";

export default function ChatPage() {
  const session = useWorkspaceSession();
  const [sessions, setSessions] = useState<ChatSessionDTO[]>([]);
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessageDTO[]>([]);
  const [inputQuestion, setInputQuestion] = useState("");
  const [loading, setLoading] = useState(false);
  const [previewCitation, setPreviewCitation] = useState<CitationDetail | null>(null);
  const [error, setError] = useState("");

  // Accessibility: role="status" on loading, role="alert" on errors, aria-current on active session
  ...
}
```

---

## Shared Patterns

### Error Handling & Responses
- FastAPI routes raise `HTTPException(status_code, detail="thông điệp tiếng Việt cụ thể")`.
- Frontend displays error banners with `role="alert"` and CSS class `error`.

### Live Scope Recheck Pattern
- Every citation preview lookup and historical message retrieval rechecks dataset permissions using `recheck_response(db, account, {dataset_id})`.
- If revoked, return `403` with detail `Quyền truy cập nguồn dữ liệu đã thay đổi hoặc bị thu hồi. Liên hệ Quản trị viên để được cấp lại quyền.`

### Module Boundaries
- `app/rag` and `app/llm` define pure business contracts and protocols.
- `app/providers` implements OpenAI adapters.
- Integration tests mock external OpenAI API calls via `FakeEmbeddingAdapter` and `FakeLLMAdapter`.

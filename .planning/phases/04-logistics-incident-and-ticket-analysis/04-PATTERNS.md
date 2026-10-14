# Phase 04: Logistics Incident and Ticket Analysis - Pattern Map

**Mapped:** 2026-10-14  
**Files analyzed:** 16  
**Analogs found:** 16 / 16  

---

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|---|---|---|---|---|
| `backend/app/modules/tickets/contracts.py` | contracts / DTO | schema definition | `backend/app/rag/contracts.py` | exact |
| `backend/app/modules/tickets/validator.py` | service / validation | data parsing & validation | `backend/app/rag/parsers/structured.py` | exact |
| `backend/app/modules/tickets/service.py` | service | intake & persistence | `backend/app/rag/service.py` | exact |
| `backend/app/modules/log_analysis/contracts.py` | contracts / DTO | schema definition | `backend/app/llm/contracts.py` | exact |
| `backend/app/modules/log_analysis/correlator.py` | service / engine | log correlation & timestamping | `backend/app/rag/retriever.py` | exact |
| `backend/app/modules/log_analysis/reasoner.py` | service / reasoning | prompt assembly & LLM analysis | `backend/app/rag/service.py` | exact |
| `backend/app/modules/log_analysis/service.py` | service | orchestration & persistence | `backend/app/rag/service.py` | exact |
| `backend/app/database/models/incident.py` | model | SQLAlchemy ORM entity | `backend/app/database/models/chat.py` | exact |
| `backend/app/api/incidents.py` | route controller | HTTP endpoints | `backend/app/api/chat.py` | exact |
| `frontend/src/app/(workspace)/incidents/page.tsx` | page component | interactive state & API calls | `frontend/src/app/(workspace)/chat/page.tsx` | exact |
| `frontend/src/components/Timeline.tsx` | UI component | chronological visualization | `frontend/src/components/EvidencePreview.tsx` | role-match |
| `frontend/src/components/Sidebar.tsx` | navigation | link rendering | `frontend/src/components/Sidebar.tsx` | exact |
| `backend/tests/unit/test_ticket_validator.py` | test | unit verification | `backend/tests/unit/test_parsers.py` | exact |
| `backend/tests/unit/test_log_correlator.py` | test | unit verification | `backend/tests/unit/test_retriever.py` | exact |
| `backend/tests/unit/test_incident_reasoner.py` | test | unit verification | `backend/tests/unit/test_openai_provider.py` | exact |
| `backend/tests/integration/test_incident_api.py` | test | integration / policy test | `backend/tests/integration/test_chat_api.py` | exact |

---

## Pattern Assignments

### 1. Pydantic V2 Strict Contract Pattern (`contracts.py`)

**Analog:** `backend/app/rag/contracts.py` and `backend/app/llm/contracts.py`

**Rules:**
- All DTOs must inherit from Pydantic `BaseModel` with `extra="forbid"` and `frozen=True` where immutable.
- Enums should be `str, Enum` for clean JSON serialization.

```python
from enum import Enum
from pydantic import BaseModel, ConfigDict, Field
from typing import Optional

class SystemEnum(str, Enum):
    WMS = "WMS"
    TMS = "TMS"
    API_GATEWAY = "API_GATEWAY"
    ERP = "ERP"
    INVENTORY = "INVENTORY"
    OTHER = "OTHER"

class PriorityEnum(str, Enum):
    P1 = "P1"
    P2 = "P2"
    P3 = "P3"
    P4 = "P4"

class TicketImportRow(BaseModel):
    model_config = ConfigDict(extra="forbid")
    ticket_id: str = Field(..., pattern=r"^[A-Z0-9_-]+$")
    order_id: str
    timestamp: str
    system: SystemEnum
    severity: PriorityEnum
    description: str = Field(..., min_length=5, max_length=2000)
```

### 2. Line-Level Error Validation Pattern (`validator.py`)

**Analog:** `backend/app/rag/parsers/structured.py`

**Rules:**
- Ingest either JSON array or CSV text.
- Inspect each row, track line number (1-indexed, taking header into account).
- Accumulate all validation errors into a structured error list rather than failing on the first line.

```python
class LineValidationError(BaseModel):
    line: int
    field: Optional[str] = None
    message: str

class ValidationResult(BaseModel):
    is_valid: bool
    tickets: list[TicketImportRow] = []
    errors: list[LineValidationError] = []
```

### 3. Cross-System Log Correlation Pattern (`correlator.py`)

**Analog:** `backend/app/rag/retriever.py`

**Rules:**
- Exact match on `order_id` (e.g. `DH001`) with word boundaries (`r"\b" + re.escape(order_id) + r"\b"`), completely ignoring similar tokens like `DH010`.
- Extract timestamps and sort events chronologically.
- Pinpoint `is_failure_point = True` on the earliest failure/timeout record (e.g. status 504 / ERROR level).

### 4. Live Scope Recheck Pattern (`api/incidents.py`)

**Analog:** `backend/app/api/chat.py` (line 197-208)

**Rules:**
- Before returning any incident analysis or opening a citation snippet, recheck the user's current dataset grants:
```python
policy = AccessPolicy(db)
current_grants = policy.get_accessible_dataset_ids(current_user.account_id)
if chunk.dataset_id not in current_grants:
    raise HTTPException(status_code=403, detail="Quyền truy cập nguồn dữ liệu đã thay đổi hoặc bị thu hồi")
```

### 5. Multi-System Visual Timeline Pattern (`Timeline.tsx`)

**Analog:** `frontend/src/app/(workspace)/chat/page.tsx`

**Rules:**
- Tag systems with distinct badge colors:
  - WMS: Blue (`bg-blue-100 text-blue-800 border-blue-300`)
  - API Gateway: Purple (`bg-purple-100 text-purple-800 border-purple-300`)
  - TMS: Orange (`bg-amber-100 text-amber-800 border-amber-300`)
- Highlight failure node with prominent red border: `border-2 border-red-500 bg-red-50/50`.
- Clicking node opens log preview drawer displaying raw log snippet and source provenance (file name, line number).

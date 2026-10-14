# Phase 05: On-Demand Incident Reports and PDF - Pattern Map

**Mapped:** 2026-10-14  
**Files analyzed:** 12  
**Analogs found:** 12 / 12  

---

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|---|---|---|---|---|
| `backend/app/modules/reports/contracts.py` | contracts / DTO | schema definition | `backend/app/modules/log_analysis/contracts.py` | exact |
| `backend/app/modules/reports/service.py` | service | SQL aggregation & metrics | `backend/app/modules/log_analysis/service.py` | exact |
| `backend/app/modules/reports/pdf_generator.py` | service / compiler | HTML/CSS to PDF | `backend/app/rag/parsers/docling_parser.py` | role-match |
| `backend/app/modules/reports/templates/incident_report.html` | template | Jinja2 print styling | `frontend/src/components/Timeline.tsx` | role-match |
| `backend/app/database/models.py` | model | SQLAlchemy ORM entity | `backend/app/database/models.py` (IncidentAnalysis) | exact |
| `backend/alembic/versions/0005_incident_reports.py` | migration | database schema | `backend/alembic/versions/0004_incident_analysis.py` | exact |
| `backend/app/api/reports.py` | route controller | HTTP endpoints & PDF streaming | `backend/app/api/incidents.py` | exact |
| `backend/app/api/health.py` | health check | DB version checking | `backend/app/api/health.py` | exact |
| `frontend/src/app/(workspace)/reports/page.tsx` | page component | two-tab workspace & preview | `frontend/src/app/(workspace)/incidents/page.tsx` | exact |
| `frontend/src/components/Sidebar.tsx` | navigation | link rendering | `frontend/src/components/Sidebar.tsx` | exact |
| `backend/tests/unit/test_report_service.py` | test | unit verification | `backend/tests/unit/test_incident_reasoner.py` | exact |
| `backend/tests/integration/test_reports_api.py` | test | integration & Live Scope Recheck | `backend/tests/integration/test_incident_api.py` | exact |

---

## Pattern Assignments

### 1. Pydantic V2 Strict Contract Pattern (`contracts.py`)

**Analog:** `backend/app/modules/log_analysis/contracts.py`

**Rules:**
- All DTOs must inherit from Pydantic `BaseModel` with `extra="forbid"` and `frozen=True`.
- Enums must be `str, Enum` for clean JSON serialization (`PeriodTypeEnum: daily, weekly, monthly, custom`).

```python
from enum import Enum
from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List, Dict, Any

class PeriodTypeEnum(str, Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    CUSTOM = "custom"
```

### 2. Live Scope Recheck & Persistence Pattern (`service.py` & `reports.py`)

**Analog:** `backend/app/modules/log_analysis/service.py` & `backend/app/api/incidents.py`

**Rules:**
- Before returning report details or compiling PDF, recheck current user `allowed_dataset_ids`.
- If user does not have permission for ANY dataset in `report.dataset_ids`, raise `HTTPException(status_code=403, detail="Quyền truy cập vào dữ liệu báo cáo đã bị thu hồi")`.

```python
# Live Scope Recheck pattern
if not user.is_admin:
    revoked = set(report.dataset_ids) - set(allowed_dataset_ids)
    if revoked:
        raise HTTPException(status_code=403, detail="Quyền truy cập vào dữ liệu báo cáo đã bị thu hồi")
```

### 3. WeasyPrint PDF Generation Pattern (`pdf_generator.py`)

**Analog:** `WeasyPrint` with Jinja2 `FileSystemLoader`

**Rules:**
- Load template with Jinja2 environment.
- Render HTML string with context dictionary.
- Render PDF bytes with `HTML(string=html_content).write_pdf()`.
- Return `StreamingResponse(io.BytesIO(pdf_bytes), media_type="application/pdf", headers={"Content-Disposition": f"attachment; filename={filename}"})`.

### 4. Health Check Version Whitelist Pattern (`health.py`)

**Analog:** `backend/app/api/health.py` lines 18-23

**Rules:**
- `alembic_version` whitelist in `database_ready()` MUST include `"0005_incident_reports"`.
- `backend/tests/integration/test_migrations.py` MUST be updated to accept `"0005_incident_reports"`.

### 5. Two-Tab Workspace Frontend Pattern (`page.tsx`)

**Analog:** `frontend/src/app/(workspace)/incidents/page.tsx`

**Rules:**
- State `activeTab: "create" | "history"`.
- Preview modal / drawer rendering deterministic KPI cards, distribution table, recurring error table, and LLM narrative.
- Provenance modal allowing inspection of source files and active versions used in the report.

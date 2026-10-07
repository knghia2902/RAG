# Phase 2: Dataset Ingestion and Source Lifecycle - Pattern Map

**Mapped:** 2026-10-07  
**Files analyzed:** 27 proposed files across backend API, database, RAG parser layer, worker queue, migration, frontend workspace, and test suites  
**Analogs found:** 27 / 27 (Existing Phase 1 production patterns provide high-fidelity structural, security, and architectural baselines)

---

## Evidence and Naming Status

Following the completion of Phase 1 (Local Workspace and Access Control), the repository transitioned from greenfield scaffolding to an established modular monolith. Tracked code in `backend/app/`, `backend/alembic/`, `frontend/src/`, and corresponding test directories establishes clear conventions:
- **API routes:** Fast, thin route handlers with FastAPI dependency injection (`Depends(get_account)`, `Depends(mutation_manager)`, `Depends(get_db)`), strict DTO validation (`model_config = ConfigDict(extra="forbid")`), and HTTP status semantics.
- **Database services:** Centralized transaction boundaries, PostgreSQL dialect upserts (`on_conflict_do_nothing`), explicit authorization checks before querying, and live pre-response scope rechecking (`recheck_response`).
- **Authorization policy:** Backend-owned `Principal`, role-based capabilities (`CAPABILITIES`), and dataset-scoped queries (`dataset_query`).
- **RAG boundary contracts:** Provider-free boundary DTOs (`SourceLocator`, `EvidenceChunk`, `BoundaryDTO`) and typing protocols (`Parser`).
- **Frontend architecture:** Next.js App Router, same-origin cookie proxying, CSRF protection, centralized fetch client (`api<T>()`), accessible Vietnamese modals with focus management and `aria-busy` state locks.
- **Infrastructure & Testing:** Docker Compose with isolated PostgreSQL/healthchecks, Alembic migrations, Pytest integration tests using `TestClient`, and Playwright E2E suites.

Phase 2 introduces file upload, multi-format parsing, immutable source versioning, durable background jobs (Celery + RabbitMQ), row/record schema validation, and parsed preview with precise locators. Every new component has a direct analog in Phase 1.

---

## File Classification

| Proposed File / Path | Role | Data Flow | Closest Analog | Match Quality |
|---|---|---|---|---|
| `backend/app/api/sources.py` | route | request-response, file-I/O | [`backend/app/api/datasets.py`](file:///D:/KhacNghia/RAG/backend/app/api/datasets.py) | High |
| `backend/app/api/schemas.py` | model (DTO) | transform | [`backend/app/api/schemas.py`](file:///D:/KhacNghia/RAG/backend/app/api/schemas.py) | Exact |
| `backend/app/api/dependencies.py` | middleware / guard | request-response | [`backend/app/api/dependencies.py`](file:///D:/KhacNghia/RAG/backend/app/api/dependencies.py) | Exact |
| `backend/app/main.py` | controller / entrypoint | request-response | [`backend/app/main.py`](file:///D:/KhacNghia/RAG/backend/app/main.py) | Exact |
| `backend/app/database/models.py` | model | CRUD | [`backend/app/database/models.py`](file:///D:/KhacNghia/RAG/backend/app/database/models.py) | Exact |
| `backend/app/database/sources.py` | service | CRUD, file-I/O | [`backend/app/database/datasets.py`](file:///D:/KhacNghia/RAG/backend/app/database/datasets.py) | High |
| `backend/app/rag/contracts.py` | boundary DTO / protocol | transform | [`backend/app/rag/contracts.py`](file:///D:/KhacNghia/RAG/backend/app/rag/contracts.py) | Exact |
| `backend/app/rag/parsers/base.py` | boundary / protocol | transform | [`backend/app/rag/contracts.py`](file:///D:/KhacNghia/RAG/backend/app/rag/contracts.py) | High |
| `backend/app/rag/parsers/profiles.py` | model / validator | transform | [`backend/app/api/schemas.py`](file:///D:/KhacNghia/RAG/backend/app/api/schemas.py) | High |
| `backend/app/rag/parsers/docling_adapter.py` | adapter / service | transform | [`backend/app/rag/contracts.py`](file:///D:/KhacNghia/RAG/backend/app/rag/contracts.py) | Medium |
| `backend/app/rag/parsers/spreadsheet.py` | adapter / service | transform | [`backend/app/rag/contracts.py`](file:///D:/KhacNghia/RAG/backend/app/rag/contracts.py) | Medium |
| `backend/app/rag/parsers/structured.py` | adapter / service | transform | [`backend/app/rag/contracts.py`](file:///D:/KhacNghia/RAG/backend/app/rag/contracts.py) | Medium |
| `backend/app/rag/parsers/text_log.py` | adapter / service | transform | [`backend/app/rag/contracts.py`](file:///D:/KhacNghia/RAG/backend/app/rag/contracts.py) | Medium |
| `backend/app/workers/celery_app.py` | provider / config | event-driven | [`backend/app/database/session.py`](file:///D:/KhacNghia/RAG/backend/app/database/session.py) | Medium |
| `backend/app/workers/tasks.py` | worker / job handler | batch, event-driven | [`backend/app/database/datasets.py`](file:///D:/KhacNghia/RAG/backend/app/database/datasets.py) | High |
| `backend/alembic/versions/0002_source_lifecycle.py` | migration | batch | [`backend/alembic/versions/0001_access_control.py`](file:///D:/KhacNghia/RAG/backend/alembic/versions/0001_access_control.py) | Exact |
| `docker-compose.yml` | config | event-driven, file-I/O | [`docker-compose.yml`](file:///D:/KhacNghia/RAG/docker-compose.yml) | Exact |
| `backend/pyproject.toml` | config | batch | [`backend/pyproject.toml`](file:///D:/KhacNghia/RAG/backend/pyproject.toml) | Exact |
| `frontend/src/app/(workspace)/datasets/page.tsx` | component | CRUD, event-driven | [`frontend/src/app/(workspace)/datasets/page.tsx`](file:///D:/KhacNghia/RAG/frontend/src/app/(workspace)/datasets/page.tsx) | Exact |
| `frontend/src/lib/contracts.ts` | utility (types) | transform | [`frontend/src/lib/contracts.ts`](file:///D:/KhacNghia/RAG/frontend/src/lib/contracts.ts) | Exact |
| `frontend/src/lib/api.ts` | utility (client) | request-response | [`frontend/src/lib/api.ts`](file:///D:/KhacNghia/RAG/frontend/src/lib/api.ts) | Exact |
| `backend/tests/unit/test_source_profiles.py` | test | transform | [`backend/tests/unit/test_policy.py`](file:///D:/KhacNghia/RAG/backend/tests/unit/test_policy.py) | High |
| `backend/tests/unit/test_source_parsers.py` | test | transform | [`backend/tests/unit/test_module_boundaries.py`](file:///D:/KhacNghia/RAG/backend/tests/unit/test_module_boundaries.py) | High |
| `backend/tests/integration/test_sources.py` | test | request-response, file-I/O | [`backend/tests/integration/test_acl.py`](file:///D:/KhacNghia/RAG/backend/tests/integration/test_acl.py) | High |
| `backend/tests/integration/test_ingestion_jobs.py` | test | batch, event-driven | [`backend/tests/integration/test_bootstrap_seed.py`](file:///D:/KhacNghia/RAG/backend/tests/integration/test_bootstrap_seed.py) | High |
| `backend/tests/integration/test_source_access.py` | test | request-response | [`backend/tests/integration/test_acl.py`](file:///D:/KhacNghia/RAG/backend/tests/integration/test_acl.py) | High |
| `backend/tests/integration/test_source_lifecycle.py` | test | CRUD | [`backend/tests/integration/test_admin_users.py`](file:///D:/KhacNghia/RAG/backend/tests/integration/test_admin_users.py) | High |
| `frontend/tests/e2e/source-ingestion.spec.ts` | test | request-response, event-driven | [`frontend/tests/e2e/datasets.spec.ts`](file:///D:/KhacNghia/RAG/frontend/tests/e2e/datasets.spec.ts) | High |

---

## Pattern Assignments

### 1. Source API and Request Guards

**Files:** `backend/app/api/sources.py`, `backend/app/api/schemas.py`, `backend/app/main.py`  
**Analog:** [`backend/app/api/datasets.py`](file:///D:/KhacNghia/RAG/backend/app/api/datasets.py#L9-L30) and [`backend/app/api/users.py`](file:///D:/KhacNghia/RAG/backend/app/api/users.py#L21-L30)

```python
# From backend/app/api/datasets.py:9-30
router = APIRouter(prefix="/api/v1", tags=["datasets"])

@router.get("/datasets", response_model=DatasetPage)
def list_datasets(page: int = Query(1, ge=1), page_size: int = Query(25, ge=1, le=100), account=Depends(get_account), db=Depends(get_db)):
    return datasets.list_metadata(db, account, page, page_size)

@router.get("/datasets/{dataset_id}", response_model=DatasetDTO)
def detail(dataset_id: UUID, account=Depends(get_account), db=Depends(get_db)):
    return datasets.detail_metadata(db, account, dataset_id)

@router.post("/admin/datasets", response_model=DatasetDTO, status_code=201)
def create(payload: DatasetCreate, account=Depends(mutation_manager), db=Depends(get_db)):
    return datasets.save_metadata(db, account, payload)
```

```python
# From backend/app/api/users.py:21-30
def mutation_manager(request: Request, db=Depends(get_db)):
    validate_request(request)
    from app.database.models import AdminGuard
    db.execute(select(AdminGuard).where(AdminGuard.id == 1).with_for_update()).scalar_one()
    identity = resolve_session(db, request.cookies.get(SESSION_COOKIE))
    validate_csrf(request, identity[0])
    return manager(identity[1])
```

#### Application to Phase 2:
- `backend/app/api/sources.py` defines routes nested under `/api/v1/datasets/{dataset_id}/sources`:
  - `POST /admin/datasets/{dataset_id}/sources/upload`: Multi-file upload via `files: list[UploadFile] = File(...)` with `profile_id: str = Form(...)`. Uses `Depends(mutation_manager)` and `Depends(get_db)` to ensure Admin role, valid session, CSRF token, and mutation serialization.
  - `GET /datasets/{dataset_id}/sources`: Paginated list of sources for authorized users (Admin or permitted Technician), using `Depends(get_account)`.
  - `GET /datasets/{dataset_id}/sources/{source_id}`: Source metadata, active version, and current job status.
  - `GET /datasets/{dataset_id}/sources/{source_id}/preview`: Paginated parsed evidence chunks/excerpts with exact `SourceLocator` coordinates. Accessible to permitted users; returns parsed text only (never local filesystem paths or static URLs).
  - `POST /admin/datasets/{dataset_id}/sources/{source_id}/retry`: Retries failed ingestion job. Requires `Depends(mutation_manager)`.
  - `POST /admin/datasets/{dataset_id}/sources/{source_id}/reprocess`: Triggers re-parsing of active/existing version under a new parse run without changing source version. Requires `Depends(mutation_manager)`.
  - `DELETE /admin/datasets/{dataset_id}/sources/{source_id}`: Immediately tombstones the source and sets cancellation fencing for running jobs. Requires `Depends(mutation_manager)`.
- `backend/app/api/schemas.py` is extended with frozen DTOs inheriting from `DTO`:
  - `SourceDTO`, `SourceVersionDTO`, `IngestionJobDTO`, `SourcePage`, `EvidencePreviewDTO`, `UploadResultItemDTO`, `UploadBatchResponseDTO`.
- `backend/app/main.py` includes `sources_router` following lines 20-27.

---

### 2. Database Models and Persistence Service

**Files:** `backend/app/database/models.py`, `backend/app/database/sources.py`  
**Analog:** [`backend/app/database/models.py`](file:///D:/KhacNghia/RAG/backend/app/database/models.py#L42-L55) and [`backend/app/database/datasets.py`](file:///D:/KhacNghia/RAG/backend/app/database/datasets.py#L43-L85)

```python
# From backend/app/database/models.py:8-10, 42-55
def utcnow():
    return datetime.now(timezone.utc)

class Dataset(Base):
    __tablename__ = "datasets"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    description: Mapped[str] = mapped_column(String(2000), default="", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

class DatasetGrant(Base):
    __tablename__ = "dataset_grants"
    account_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("accounts.id"), primary_key=True)
    dataset_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("datasets.id"), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
```

```python
# From backend/app/database/datasets.py:43-58
def recheck_response(db, account, initial_scope, detail=False):
    # READ COMMITTED + fresh SQL, never the session identity-map snapshot.
    current_scope = allowed_dataset_ids(db, account)
    if not initial_scope.issubset(current_scope):
        raise HTTPException(404 if detail else 403, "Không tìm thấy Dataset" if detail else "Quyền truy cập đã thay đổi")

def list_metadata(db, account, page, page_size):
    account = current_account(db, account)
    scope = allowed_dataset_ids(db, account)
    query = dataset_query(account).where(Dataset.id.in_(scope))
    total = db.scalar(select(func.count()).select_from(query.subquery()))
    rows = db.scalars(query.order_by(Dataset.created_at, Dataset.id).offset((page-1)*page_size).limit(page_size)).all()
    result = DatasetPage(items=[DatasetDTO.model_validate(row) for row in rows], total=total, page=page, page_size=page_size)
    recheck_response(db, account, scope)
    return result
```

#### Application to Phase 2:
- **Models (`backend/app/database/models.py`):**
  - `Source`: `id` (UUID), `dataset_id` (FK to `datasets.id`, index), `logical_filename` (String 255), `profile_id` (String 64), `active_version_id` (UUID, nullable, FK to `source_versions.id`), `deleted_at` (DateTime, nullable for tombstoning), `created_at` (DateTime), `updated_at` (DateTime). Unique constraint on `(dataset_id, logical_filename)` where `deleted_at IS NULL`.
  - `SourceVersion`: `id` (UUID), `source_id` (FK to `sources.id`), `version_number` (Integer, positive), `content_hash` (String 64, SHA-256), `storage_key` (String 255, opaque path in private storage), `size_bytes` (Integer), `mime_type` (String 64), `created_at` (DateTime). Unique constraint on `(source_id, version_number)`.
  - `ImportJob`: `id` (UUID), `source_version_id` (FK to `source_versions.id`), `state` (Enum/String: `queued`, `processing`, `ready`, `failed`), `attempt_count` (Integer, default 0), `max_attempts` (Integer, default 3), `lease_expires_at` (DateTime, nullable), `error_code` (String, nullable), `error_message` (String, nullable), `diagnostics` (JSONB, nullable: row/record errors), `created_at` (DateTime), `updated_at` (DateTime).
  - `ParseRun`: `id` (UUID), `source_version_id` (FK), `job_id` (FK), `parser_name` (String), `parser_version` (String), `status` (`staged`, `published`, `failed`), `created_at`.
  - `CanonicalRecord` / `ParsedChunk`: `id` (UUID), `parse_run_id` (FK), `source_version_id` (FK), `dataset_id` (FK), `position` (Integer), `locator_data` (JSONB - page, section, sheet, row, line_start, line_end, json_path), `content_text` (String), `record_metadata` (JSONB - normalized IDs, timestamps, status, priority).
- **Service (`backend/app/database/sources.py`):**
  - Enforces `require_admin` for mutations, and `allowed_dataset_ids(db, account)` for queries.
  - Implements `recheck_response(db, account, {dataset_id})` immediately before returning source details or parsed evidence previews (satisfies ASVS V8 and `docs/security-contracts.md`).
  - Implements **Atomic Version Activation**:
    ```python
    def activate_source_version(db, source_id, version_id, parse_run_id):
        # 1. Verify source is not tombstoned (fencing)
        source = db.get(Source, source_id)
        if not source or source.deleted_at is not None:
            raise IngestionFencedError("Source tombstoned")
        # 2. Verify all required records staged and parse_run is valid
        # 3. Update source.active_version_id atomically
        source.active_version_id = version_id
        # 4. Mark parse_run published
        parse_run = db.get(ParseRun, parse_run_id)
        parse_run.status = "published"
        db.commit()
    ```
  - Implements **Idempotent Deduplication**: Same SHA-256 in same dataset returns existing source/version without staging duplicate records.

---

### 3. RAG Contracts and Source Profiles

**Files:** `backend/app/rag/contracts.py`, `backend/app/rag/parsers/base.py`, `backend/app/rag/parsers/profiles.py`  
**Analog:** [`backend/app/rag/contracts.py`](file:///D:/KhacNghia/RAG/backend/app/rag/contracts.py#L6-L48)

```python
# From backend/app/rag/contracts.py:6-23, 36-48
Position = Annotated[int, Field(strict=True, ge=1, le=2147483647)]
LocatorText = Annotated[str, Field(min_length=1, max_length=512)]

class SourceLocator(BoundaryDTO):
    source_id: UUID
    source_version: Position
    page: Position | None = None
    section: LocatorText | None = None
    sheet: LocatorText | None = None
    row: Position | None = None
    event: Position | None = None
    record: Position | None = None

class EvidenceChunk(BoundaryDTO):
    dataset_id: UUID
    locator: SourceLocator
    text: str = Field(min_length=1, max_length=32000)

class Parser(Protocol):
    def parse(self, content: bytes, locator: SourceLocator, dataset_id: UUID) -> tuple[EvidenceChunk, ...]: ...
```

#### Application to Phase 2:
- `backend/app/rag/contracts.py`:
  - Extend `SourceLocator` to support log line ranges and JSON paths as required by DATA-04 and CONTEXT D-08:
    ```python
    class SourceLocator(BoundaryDTO):
        source_id: UUID
        source_version: Position
        page: Position | None = None
        section: LocatorText | None = None
        sheet: LocatorText | None = None
        row: Position | None = None
        event: Position | None = None
        record: Position | None = None
        line_start: Position | None = None
        line_end: Position | None = None
        json_path: LocatorText | None = None
    ```
- `backend/app/rag/parsers/base.py`:
  - Defines `ParsedRecord`, `ParserDiagnostic`, and `ParseResult` boundary models.
  - Maintains strict protocol typing for format adapters without importing database sessions or LLM clients.
- `backend/app/rag/parsers/profiles.py`:
  - Defines published schemas for DATA-06:
    - `document`: General text/SOP; requires extracted text, captures page/section/headings.
    - `log`: Server/app logs; requires `timestamp` (ISO-8601 UTC), `system`, `severity`; optional `trace_id`, `message`. Captures line/event locators.
    - `ticket`: Support/service tickets; requires `ticket_id`, `system`, `status`, `priority`, `opened_at`; optional `resolved_at`, `assignee`.
    - `incident`: Operations incidents; requires `incident_id`, `system`, `status`, `priority`, `created_at`; optional `confirmed_cause`.
    - `operations_table`: Structured tabular data; requires primary identifier, entity status, timestamp.
  - Returns structured validation diagnostics with exact `row` or `record_index`, invalid field name, and actionable error reason.

---

### 4. Format Parser Adapters

**Files:** `backend/app/rag/parsers/docling_adapter.py`, `backend/app/rag/parsers/spreadsheet.py`, `backend/app/rag/parsers/structured.py`, `backend/app/rag/parsers/text_log.py`  
**Analog:** [`backend/app/rag/contracts.py`](file:///D:/KhacNghia/RAG/backend/app/rag/contracts.py#L47-L48)

```python
# Protocol pattern from contracts.py
class Parser(Protocol):
    def parse(self, content: bytes, locator: SourceLocator, dataset_id: UUID) -> tuple[EvidenceChunk, ...]: ...
```

#### Application to Phase 2:
- **Docling Adapter (`docling_adapter.py`):**
  - Parses PDF and DOCX files.
  - **CRITICAL:** Explicitly sets `do_ocr=False` in `PipelineOptions`.
  - Scanned PDF detection: If extracted text is empty or non-existent on pages, raises `UnsupportedFormatError("File PDF không có văn bản hoặc là bản scan. OCR không được hỗ trợ trong phiên bản này.")`.
  - Maps Docling's `ProvenanceItem` (page numbers 1-indexed) into `SourceLocator(page=..., section=...)`.
- **Spreadsheet Adapter (`spreadsheet.py`):**
  - Parses XLSX using `openpyxl` with `read_only=True` to stream large sheets with bounded memory. Always closes workbooks in `finally:` blocks.
  - Parses CSV using Python `csv.reader` / `csv.DictReader`.
  - Retains header offset, sheet name, and 1-indexed row number into `SourceLocator(sheet=..., row=...)`.
- **Structured Adapter (`structured.py`):**
  - Parses JSON and JSONL (line-delimited JSON).
  - Uses `json.loads` per line for JSONL; tracks record index and RFC 6901 JSON pointer paths into `SourceLocator(record=..., json_path=...)`.
- **Text & Log Adapter (`text_log.py`):**
  - Parses plain `.txt` and `.log` files line-by-line.
  - Records exact 1-indexed line start and line end into `SourceLocator(line_start=..., line_end=..., event=...)`.

---

### 5. Durable Queue and Celery Workers

**Files:** `backend/app/workers/celery_app.py`, `backend/app/workers/tasks.py`  
**Analog:** [`backend/app/database/session.py`](file:///D:/KhacNghia/RAG/backend/app/database/session.py#L1-L15) and [`backend/app/database/datasets.py`](file:///D:/KhacNghia/RAG/backend/app/database/datasets.py#L26-L41)

```python
# Session and transaction pattern from session.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

engine = create_engine(settings.database_url, ...)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
```

```python
# Mutation and audit pattern from datasets.py
def set_grant(db, actor, target_id, dataset_id, present):
    require_admin(current_account(db, actor))
    technician_target(db, target_id)
    ...
    db.commit()
    logger.warning("actor=%s action=%s account=%s dataset=%s", actor.id, "dataset.grant", target_id, dataset_id)
```

#### Application to Phase 2:
- **Celery Configuration (`backend/app/workers/celery_app.py`):**
  - Configures Celery instance with RabbitMQ broker (`amqp://rag:password@rabbitmq:5672//`).
  - Sets durable task routing, `task_acks_late = True`, `task_reject_on_worker_lost = True`, `task_serializer = "json"`.
  - Dispatches *only* lightweight identifiers: `job_id: str` and `source_version_id: str` (never raw file contents or file bytes).
- **Task Implementation (`backend/app/workers/tasks.py`):**
  - `process_ingestion_job(job_id: str)`:
    1. Loads `ImportJob` from PostgreSQL using a fresh `SessionLocal()`.
    2. Checks job state and cancellation fencing: if source was deleted (`deleted_at IS NOT NULL`), aborts immediately.
    3. Acquires worker lease on job row (`state = 'processing'`, `lease_expires_at = utcnow() + 10m`).
    4. Reads original file from private storage path (`storage/sources/{storage_key}`).
    5. Calls corresponding format adapter and validates against selected profile schema.
    6. If validation fails on required fields/structure: records row/record errors in `job.diagnostics`, sets `job.state = 'failed'`, and leaves old active version untouched (Atomic Failure Guarantee, D-02).
    7. If valid: stages records into `canonical_records`, switches `source.active_version_id` atomically, sets `job.state = 'ready'`, and commits transaction.
    8. Handles transient errors with bounded backoff (max 3 retries); permanent/validation errors transition directly to `failed`.

---

### 6. Migrations and Deployment Configuration

**Files:** `backend/alembic/versions/0002_source_lifecycle.py`, `docker-compose.yml`, `backend/pyproject.toml`  
**Analog:** [`backend/alembic/versions/0001_access_control.py`](file:///D:/KhacNghia/RAG/backend/alembic/versions/0001_access_control.py#L12-L58) and [`docker-compose.yml`](file:///D:/KhacNghia/RAG/docker-compose.yml#L2-L53)

```python
# From backend/alembic/versions/0001_access_control.py:12-42
def upgrade():
    op.create_table("datasets", sa.Column("id", pg.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(128), nullable=False, unique=True),
        sa.Column("description", sa.String(2000), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False))
```

```yaml
# From docker-compose.yml:46-52
  backend:
    <<: *backend
    environment: *operational-env
    volumes: [./data/uploads:/app/data/uploads, ./storage:/app/storage]
    healthcheck: *api-health
    depends_on:
      migrate: {condition: service_completed_successfully}
```

#### Application to Phase 2:
- **Migration (`0002_source_lifecycle.py`):**
  - Sets `down_revision = "0001_access_control"`.
  - Creates tables: `sources`, `source_versions`, `import_jobs`, `parse_runs`, `canonical_records`.
  - Adds indices on foreign keys and compound unique index `ix_sources_dataset_filename` with condition `deleted_at IS NULL`.
- **Compose (`docker-compose.yml`):**
  - Adds `rabbitmq` service (`rabbitmq:4.3.6-management`) with healthcheck and persistent volume `rabbitmq-data`.
  - Adds `worker` service sharing the `*backend` build definition and mounting `./storage:/app/storage` (private source storage volume).
  - Updates `backend` and `backend-test` dependencies to ensure RabbitMQ is healthy before starting.
- **Dependencies (`backend/pyproject.toml`):**
  - Adds candidate packages `python-multipart`, `docling`, `openpyxl`, `celery` following the mandatory `checkpoint:human-verify` protocol.

---

### 7. Frontend Dataset Workspace and Transport

**Files:** `frontend/src/app/(workspace)/datasets/page.tsx`, `frontend/src/lib/contracts.ts`, `frontend/src/lib/api.ts`  
**Analog:** [`frontend/src/app/(workspace)/datasets/page.tsx`](file:///D:/KhacNghia/RAG/frontend/src/app/(workspace)/datasets/page.tsx#L9-L23), [`frontend/src/lib/contracts.ts`](file:///D:/KhacNghia/RAG/frontend/src/lib/contracts.ts#L1-L7), and [`frontend/src/lib/api.ts`](file:///D:/KhacNghia/RAG/frontend/src/lib/api.ts#L1-L12)

```typescript
// From frontend/src/lib/contracts.ts:3-7
export type Dataset = { id: string; name: string; description: string; created_at: string };
export type DatasetInput = Pick<Dataset, "name" | "description">;
export type DatasetGrants = { dataset_ids: string[] };
export type Page<T> = { items: T[]; total: number; page: number; page_size: number };
```

```typescript
// From frontend/src/lib/api.ts:2-10
export async function api<T>(path: string, options: { method?: string; body?: unknown; csrf?: string } = {}): Promise<T> {
  const method = options.method ?? "GET";
  const response = await fetch(`/api/v1${path}`, {
    method, credentials: "same-origin", cache: "no-store",
    headers: method === "GET" ? {} : {
      "Content-Type": "application/json",
      "X-Requested-With": "RAG-Web",
      ...(options.csrf ? { "X-CSRF-Token": options.csrf } : {})
    },
    ...(method !== "GET" ? { body: JSON.stringify(options.body ?? {}) } : {})
  });
  ...
}
```

```tsx
// Modal and table pattern from frontend/src/app/(workspace)/datasets/page.tsx:9-13
function MetadataPanel({dataset,csrf,onClose,onSaved}:{dataset:Dataset|null;csrf:string;onClose:()=>void;onSaved:()=>Promise<void>}){
  const dialog=useRef<HTMLDialogElement>(null);const mounted=useRef(false);const [busy,setBusy]=useState(false);const [error,setError]=useState("");
  useEffect(()=>{mounted.current=true;const el=dialog.current;el?.showModal();return()=>{mounted.current=false;el?.close();};},[]);
  return <dialog ref={dialog} aria-labelledby="metadata-title" aria-busy={busy} ...>...</dialog>;
}
```

#### Application to Phase 2:
- **API Client (`frontend/src/lib/api.ts`):**
  - Extends `api<T>()` or adds `uploadFiles<T>()` helper to support `FormData`.
  - When `body instanceof FormData`, leaves `Content-Type` header unset so the browser automatically populates `multipart/form-data; boundary=...`, while keeping `credentials: "same-origin"`, `X-Requested-With: "RAG-Web"`, and `X-CSRF-Token: options.csrf`.
- **Contracts (`frontend/src/lib/contracts.ts`):**
  - Extends contracts with:
    ```typescript
    export type SourceStatus = "queued" | "processing" | "ready" | "failed";
    export type Source = {
      id: string; dataset_id: string; logical_filename: string; profile_id: string;
      active_version: number | null; status: SourceStatus; error_message?: string;
      created_at: string; updated_at: string;
    };
    export type SourceLocator = {
      source_id: string; source_version: number; page?: number; section?: string;
      sheet?: string; row?: number; line_start?: number; line_end?: number; json_path?: string;
    };
    export type EvidencePreview = { text: string; locator: SourceLocator };
    export type SourceProfile = { id: string; name: string; description: string; expected_fields: string[] };
    ```
- **UI Workspace (`frontend/src/app/(workspace)/datasets/page.tsx`):**
  - Adds Source Section inside Dataset Detail:
    - **Upload Button & Modal (`UploadSourceDialog`):** Displays file dropzone/picker, published profile selection dropdown (document, log, ticket, incident, operations_table), expected fields preview, and multi-file upload progress table with individual per-file status badges.
    - **Sources Table:** Lists sources under selected dataset with columns: Tên tệp, Profile, Phiên bản active, Trạng thái (queued, processing, ready, failed), Thao tác.
    - **Action Controls:**
      - "Xem đoạn trích" (Preview): Opens `SourcePreviewModal` displaying parsed chunks with exact locator tags (Trang, Dòng, Sheet/Hàng, JSON Path).
      - "Thử lại" (Retry): Available on `failed` status for Admin.
      - "Xử lý lại" (Reprocess): Reprocesses active version for Admin.
      - "Xóa" (Delete): Admin confirmation to tombstone source.
    - All dialogs follow `dialog.showModal()`, focus trapping, `aria-busy` locks on mutation, and accessible Vietnamese labels.

---

### 8. Unit, Integration, and E2E Test Suites

**Files:**
- `backend/tests/unit/test_source_profiles.py`
- `backend/tests/unit/test_source_parsers.py`
- `backend/tests/integration/test_sources.py`
- `backend/tests/integration/test_ingestion_jobs.py`
- `backend/tests/integration/test_source_access.py`
- `backend/tests/integration/test_source_lifecycle.py`
- `frontend/tests/e2e/source-ingestion.spec.ts`

**Analog:** [`backend/tests/integration/test_acl.py`](file:///D:/KhacNghia/RAG/backend/tests/integration/test_acl.py#L24-L60), [`backend/tests/unit/test_policy.py`](file:///D:/KhacNghia/RAG/backend/tests/unit/test_policy.py#L13-L58), and [`frontend/tests/e2e/datasets.spec.ts`](file:///D:/KhacNghia/RAG/frontend/tests/e2e/datasets.spec.ts#L1-L15)

```python
# From backend/tests/integration/test_acl.py:24-36
def test_metadata_admin_validation_and_rollback(client, admin, db):
    result = client.post("/api/v1/admin/datasets", json={"name":"WMS", "description":"Nguồn vận hành"}, headers=admin)
    assert result.status_code == 201
    ...
    assert client.post("/api/v1/admin/datasets", json={"name":"No CSRF"}, headers=HEADERS).status_code == 403
```

```python
# From backend/tests/unit/test_policy.py:53-58
def test_ticket_analysis_does_not_grant_repository_management():
    tech = principal()
    assert policy.has_capability(tech, "ticket.analyze")
    for action in ("repository.upload", "repository.delete", "repository.reindex"):
        assert not policy.has_capability(tech, action)
```

#### Application to Phase 2:
- `backend/tests/unit/test_source_profiles.py`: Validates schema parsing and normalization for all five profiles (`document`, `log`, `ticket`, `incident`, `operations_table`). Tests missing required fields, invalid timestamps, timezone normalization, and row/record error positions.
- `backend/tests/unit/test_source_parsers.py`: Tests parser adapters with binary fixtures across PDF, DOCX, CSV, XLSX, TXT, JSON, JSONL, and .log. Asserts scanned PDF failure (`do_ocr=False`), multiline CSV quoting, and precise `SourceLocator` coordinates.
- `backend/tests/integration/test_sources.py`: Exercises multi-file upload API, validates per-file status in batch responses, verifies technicians receive 403 on upload, and checks private storage path masking.
- `backend/tests/integration/test_ingestion_jobs.py`: Tests durable worker execution, bounded retry on transient failure, worker crash/restart lease recovery, and idempotency (no duplicate canonical records on retry).
- `backend/tests/integration/test_source_access.py`: Verifies direct API authorization: technician cannot preview ungranted dataset sources (returns 404), active-only version visibility, and live grant revocation before response returns 403.
- `backend/tests/integration/test_source_lifecycle.py`: Tests atomic version activation (failed version never replaces active version), reprocess keeps existing version active, and immediate tombstoning fences background jobs.
- `frontend/tests/e2e/source-ingestion.spec.ts`: End-to-end browser tests verifying file upload dialog, profile selection preview, status polling, preview excerpt modal with locators, retry, and delete interactions in Vietnamese.

---

## Shared Patterns

### Shared Pattern 1: Atomic Version Activation & Staged Publication
- **Owner:** `backend/app/database/sources.py` & `backend/app/workers/tasks.py`
- **Application:** All ingestion and reprocess runs.
- **Contract:** A source version begins in candidate state. Canonical records are staged under a specific `parse_run_id`. Only when *all* required fields and validations succeed is `source.active_version_id` atomically switched in a single database transaction. If any validation fails, the job transitions to `failed`, staged records are discarded/quarantined, and the previously active version remains active and visible.

### Shared Pattern 2: Live SQL Scope Recheck on Content Serving
- **Owner:** `backend/app/database/sources.py` & `backend/app/api/sources.py`
- **Application:** Source metadata, preview excerpts, and any file download endpoints.
- **Contract:** Enforces ASVS V8 and `docs/security-contracts.md`. Calling `recheck_response(db, account, {dataset_id})` queries live database grants immediately before rendering the response. If access was revoked mid-request, returns 404/403 and zero source bytes/text.

### Shared Pattern 3: Private Storage & Path Isolation
- **Owner:** `backend/app/database/sources.py` & `backend/app/api/sources.py`
- **Application:** File upload, storage write, and preview responses.
- **Contract:** Uploaded files are stored in `/app/storage/sources/` using cryptographically generated UUID/opaque keys (`storage_key`). The directory is never mounted to static web paths. API responses expose only logical filename, version number, and parsed excerpts with locators. Local filesystem paths are never returned to clients.

### Shared Pattern 4: Job Fencing and Tombstoning
- **Owner:** `backend/app/database/sources.py` & `backend/app/workers/tasks.py`
- **Application:** Source deletion and background worker execution.
- **Contract:** Deleting a source sets `deleted_at = utcnow()` immediately (tombstone). Any in-flight worker job periodically checks `source.deleted_at`; if tombstoned, the worker terminates immediately and discards outputs without updating `active_version_id`.

### Shared Pattern 5: Actionable Row/Record Diagnostic Reporting
- **Owner:** `backend/app/rag/parsers/profiles.py` & `backend/app/workers/tasks.py`
- **Application:** Parsing, schema validation, and job error presentation.
- **Contract:** Parser validation errors never dump raw stack traces or internal server paths. Instead, errors are structured diagnostics: `{"row": 42, "record": 105, "field": "timestamp", "reason": "Invalid ISO-8601 UTC format"}` stored in `job.diagnostics`.

---

## Implementation Invariants & Guardrails

1. **No LLM / AI Provider Calls:** Phase 2 must strictly operate provider-free. No calls to OpenAI, LangChain pipelines, embeddings, or vector searches.
2. **No OCR on Scanned Files:** Docling PDF adapter must enforce `do_ocr=False`. Scanned PDFs or images must fail explicitly with user-facing Vietnamese error messages.
3. **Idempotent Multi-File Upload:** Files with identical SHA-256 in the same dataset must be no-op idempotent. Changed content under the same logical name creates a new immutable version.
4. **Active Version Isolation:** Only the `active` version of an untombstoned source can be queried for previews or included in subsequent Phase 3 indexing.
5. **CSRF & Same-Origin on Mutations:** Every upload, retry, reprocess, and delete mutation must validate `Origin: http://localhost:3000` (or configured origin), `X-Requested-With: RAG-Web`, and valid session CSRF tokens via `mutation_manager`.
6. **Package Verification:** All proposed packages (`python-multipart`, `docling`, `openpyxl`, `celery`) must pass the required `checkpoint:human-verify` before installation.

---

## Dependency Order for Planning

1. **Wave 0 (Test Scaffolding & Dependency Gate):**
   - Execute package legitimacy checkpoints for `docling`, `openpyxl`, `celery`, and `python-multipart`.
   - Update `pyproject.toml` and regenerate `requirements.lock`.
   - Create test harness files: `test_source_profiles.py`, `test_source_parsers.py`, `test_sources.py`, `test_ingestion_jobs.py`, `test_source_access.py`, `test_source_lifecycle.py`, `source-ingestion.spec.ts`.
2. **Wave 1 (Database Migration & Infrastructure):**
   - Update `docker-compose.yml` to introduce RabbitMQ broker and worker services with private storage volumes.
   - Implement Alembic migration `0002_source_lifecycle.py` and models in `backend/app/database/models.py`.
3. **Wave 2 (RAG Parser Layer & Published Profiles):**
   - Extend `SourceLocator` in `backend/app/rag/contracts.py`.
   - Implement profiles in `backend/app/rag/parsers/profiles.py`.
   - Implement format adapters: `docling_adapter.py`, `spreadsheet.py`, `structured.py`, `text_log.py`.
4. **Wave 3 (Durable Background Worker & Activation Service):**
   - Implement Celery app and task runner in `backend/app/workers/`.
   - Implement database source operations, atomic activation, and job recovery in `backend/app/database/sources.py`.
5. **Wave 4 (Backend API Routes & Authorization):**
   - Implement endpoints in `backend/app/api/sources.py` and register in `backend/app/main.py`.
   - Implement DTOs in `backend/app/api/schemas.py`.
6. **Wave 5 (Frontend Workspace & E2E Validation):**
   - Extend frontend API client in `frontend/src/lib/api.ts` for multipart upload.
   - Extend contracts in `frontend/src/lib/contracts.ts`.
   - Build UI components in `frontend/src/app/(workspace)/datasets/page.tsx`.
   - Validate full Playwright and Pytest suites.

---

## Metadata

**Analog search scope:** Production Phase 1 backend, database, auth policy, frontend workspace, and test suites.  
**Tracked files scanned:** All core application files in `backend/app/`, `backend/alembic/`, `frontend/src/`, and `tests/`.  
**Pattern extraction date:** 2026-10-07.  
**Coverage:** 27 proposed files mapped to existing codebase analogs with concrete code excerpts.  

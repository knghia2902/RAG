from datetime import datetime
from uuid import UUID
from typing import Any, Literal
from pydantic import BaseModel, ConfigDict, Field, field_validator
from app.auth.passwords import normalize_username, validate_password


class DTO(BaseModel):
    model_config = ConfigDict(extra="forbid", from_attributes=True, frozen=True)


class LoginInput(DTO):
    username: str
    password: str = Field(min_length=8, max_length=128)

    @field_validator("username")
    @classmethod
    def username_valid(cls, value):
        return normalize_username(value)


class AccountDTO(DTO):
    id: UUID
    username: str
    display_name: str
    role: Literal["admin", "technician"]
    active: bool
    must_change_password: bool
    created_at: datetime


class SessionDTO(DTO):
    account: AccountDTO
    csrf_token: str


class DatasetDTO(DTO):
    id: UUID
    name: str
    description: str
    created_at: datetime


class DatasetPage(DTO):
    items: list[DatasetDTO]
    total: int
    page: int
    page_size: int


class DatasetCreate(DTO):
    name: str = Field(min_length=1, max_length=128)
    description: str = Field(default="", max_length=2000)


class DatasetPatch(DTO):
    name: str = Field(default=None, min_length=1, max_length=128)
    description: str = Field(default=None, max_length=2000)


class DatasetGrants(DTO):
    dataset_ids: list[UUID]


class AccountCreate(DTO):
    username: str
    display_name: str = Field(min_length=1, max_length=128)
    role: Literal["admin", "technician"]
    temporary_password: str = Field(min_length=8, max_length=128)

    @field_validator("username")
    @classmethod
    def username_valid(cls,value):
        return normalize_username(value)


class AccountPatch(DTO):
    display_name: str | None = Field(default=None, min_length=1, max_length=128)
    role: Literal["admin", "technician"] | None = None
    active: bool | None = None


class PasswordReset(DTO):
    temporary_password: str = Field(min_length=8, max_length=128)


class AccountPage(DTO):
    items: list[AccountDTO]
    total: int
    page: int
    page_size: int


class SourceProfileDTO(DTO):
    id: str
    name: str
    description: str
    supported_formats: list[str]
    expected_fields: list[str]
    optional_fields: list[str]


class SourceVersionDTO(DTO):
    id: UUID
    version_number: int
    content_hash: str
    size_bytes: int
    mime_type: str
    created_at: datetime


class IngestionJobDTO(DTO):
    id: UUID
    source_version_id: UUID
    state: str
    attempt_count: int
    error_code: str | None = None
    error_message: str | None = None
    diagnostics: list[dict[str, Any]] | None = None
    created_at: datetime
    updated_at: datetime


class SourceDTO(DTO):
    id: UUID
    dataset_id: UUID
    logical_filename: str
    profile_id: str
    active_version_id: UUID | None = None
    active_version_number: int | None = None
    status: str
    error_message: str | None = None
    created_at: datetime
    updated_at: datetime


class SourcePage(DTO):
    items: list[SourceDTO]
    total: int
    page: int
    page_size: int


class UploadResultItemDTO(DTO):
    filename: str
    source_id: UUID
    version_number: int
    status: str
    job_id: UUID
    is_duplicate: bool
    message: str


class UploadBatchResponseDTO(DTO):
    items: list[UploadResultItemDTO]


class SourceLocatorDTO(DTO):
    source_id: UUID
    source_version: int
    page: int | None = None
    section: str | None = None
    sheet: str | None = None
    row: int | None = None
    event: int | None = None
    record: int | None = None
    line_start: int | None = None
    line_end: int | None = None
    json_path: str | None = None


class EvidenceExcerptDTO(DTO):
    id: UUID
    position: int
    text: str
    locator: SourceLocatorDTO
    metadata: dict[str, Any] = Field(default_factory=dict)


class EvidencePreviewPage(DTO):
    source_id: UUID
    version_number: int
    items: list[EvidenceExcerptDTO]
    total: int
    page: int
    page_size: int


class ModelConfigDTO(DTO):
    embedding_provider: str
    embedding_model: str
    embedding_dimension: int
    index_version: str
    llm_provider: str
    llm_model: str
    openai_configured: bool


class UpdateModelConfigDTO(DTO):
    llm_model: str | None = None
    embedding_model: str | None = None


class ChatSessionDTO(DTO):
    id: UUID
    title: str
    created_at: datetime
    updated_at: datetime


class ChatMessageDTO(DTO):
    id: UUID
    role: str
    content: str
    citations: list[dict[str, Any]] = Field(default_factory=list)
    has_uncertainty: bool = False
    has_conflict: bool = False
    created_at: datetime


class ChatQueryRequestDTO(DTO):
    question: str = Field(min_length=1, max_length=2000)
    session_id: UUID | None = None
    dataset_ids: list[UUID] | None = None
    profile_id: str | None = None
    start_time: datetime | None = None
    end_time: datetime | None = None


class ChatQueryResponseDTO(DTO):
    session_id: UUID
    message: ChatMessageDTO
    citations: list[dict[str, Any]] = Field(default_factory=list)


class CitationPreviewResponseDTO(DTO):
    citation_index: int
    dataset_id: UUID
    dataset_name: str
    source_id: UUID
    logical_filename: str
    version_number: int
    locator: SourceLocatorDTO
    excerpt_text: str


class AnalyzeIncidentRequestDTO(DTO):
    order_id: str = Field(min_length=3, max_length=64, pattern=r"^[A-Za-z0-9_-]+$")
    description: str | None = None
    system: str | None = None


class IncidentHistoryItemDTO(DTO):
    id: UUID
    order_id: str
    ticket_id: str | None = None
    title: str
    input_mode: str
    error_group: str
    primary_system: str
    suggested_priority: str
    created_at: datetime


class IncidentAnalysisDetailDTO(DTO):
    id: UUID
    order_id: str
    ticket_id: str | None = None
    title: str
    input_mode: str
    summary: str
    classification: dict[str, Any]
    timeline: list[dict[str, Any]]
    hypotheses: list[dict[str, Any]]
    missing_information: list[str]
    recommended_actions: list[dict[str, Any]]
    citations: list[dict[str, Any]]
    created_at: datetime




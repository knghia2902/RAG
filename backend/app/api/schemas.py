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


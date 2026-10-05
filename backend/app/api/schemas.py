from datetime import datetime
from uuid import UUID
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, field_validator
from app.auth.passwords import normalize_username, validate_password


class DTO(BaseModel):
    model_config = ConfigDict(extra="forbid", from_attributes=True)


class LoginInput(DTO):
    username: str
    password: str = Field(min_length=15, max_length=128)

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


class AccountCreate(DTO):
    username: str
    display_name: str = Field(min_length=1, max_length=128)
    role: Literal["admin", "technician"]
    temporary_password: str = Field(min_length=15, max_length=128)

    @field_validator("username")
    @classmethod
    def username_valid(cls,value):
        return normalize_username(value)


class AccountPatch(DTO):
    display_name: str | None = Field(default=None, min_length=1, max_length=128)
    role: Literal["admin", "technician"] | None = None
    active: bool | None = None


class PasswordReset(DTO):
    temporary_password: str = Field(min_length=15, max_length=128)


class AccountPage(DTO):
    items: list[AccountDTO]
    total: int
    page: int
    page_size: int

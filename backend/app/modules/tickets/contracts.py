from enum import Enum
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator
from dateutil import parser as date_parser


class SystemEnum(str, Enum):
    WMS = "WMS"
    TMS = "TMS"
    API_GATEWAY = "API_GATEWAY"
    ERP = "ERP"
    INVENTORY = "INVENTORY"
    OTHER = "OTHER"


class SeverityEnum(str, Enum):
    P1 = "P1"
    P2 = "P2"
    P3 = "P3"
    P4 = "P4"


class TicketImportRow(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    ticket_id: str = Field(..., pattern=r"^[A-Z0-9_-]+$")
    order_id: str = Field(..., min_length=1)
    timestamp: str
    system: SystemEnum
    severity: SeverityEnum
    description: str = Field(..., min_length=5, max_length=2000)
    customer_id: Optional[str] = None
    reported_by: Optional[str] = None

    @field_validator("timestamp")
    @classmethod
    def validate_timestamp_format(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Thời gian không được để trống")
        try:
            parsed = date_parser.parse(v)
            return parsed.isoformat()
        except Exception as e:
            raise ValueError(f"Định dạng thời gian không hợp lệ, yêu cầu ISO 8601: {e}")


class LineValidationError(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    line: int
    field: Optional[str] = None
    message: str
    invalid_value: Optional[str] = None


class ValidationResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    is_valid: bool
    total_rows: int
    tickets: list[TicketImportRow] = Field(default_factory=list)
    errors: list[LineValidationError] = Field(default_factory=list)

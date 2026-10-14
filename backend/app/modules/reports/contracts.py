import uuid
from datetime import date, datetime
from enum import Enum
from typing import Any, Optional
from pydantic import BaseModel, ConfigDict, Field, model_validator


class PeriodTypeEnum(str, Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    CUSTOM = "custom"


class ReportFilterDTO(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    period_type: PeriodTypeEnum
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    dataset_ids: list[uuid.UUID] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_period_dates(self) -> "ReportFilterDTO":
        if self.period_type == PeriodTypeEnum.CUSTOM:
            if self.start_date is None or self.end_date is None:
                raise ValueError("start_date và end_date là bắt buộc khi chọn kỳ tùy chọn (custom)")
        if self.start_date and self.end_date:
            if self.start_date > self.end_date:
                raise ValueError("start_date không được sau end_date")
            if (self.end_date - self.start_date).days > 366:
                raise ValueError("Khoảng thời gian báo cáo không được vượt quá 366 ngày")
        return self


class RecurringErrorItemDTO(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    system: str
    error_group: str
    occurrence_count: int
    percentage: float
    affected_orders: list[str] = Field(default_factory=list)
    sample_message: Optional[str] = None


class SystemDistributionDTO(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    system: str
    incident_count: int
    ticket_count: int
    percentage: float


class PriorityDistributionDTO(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    priority: str
    count: int
    percentage: float


class ReportMetricsDTO(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    total_incidents: int
    total_tickets: int
    resolved_incidents: int
    open_incidents: int
    mttr_minutes: Optional[float] = None
    system_breakdown: list[SystemDistributionDTO] = Field(default_factory=list)
    priority_breakdown: list[PriorityDistributionDTO] = Field(default_factory=list)
    error_group_breakdown: dict[str, int] = Field(default_factory=dict)
    recurring_errors: list[RecurringErrorItemDTO] = Field(default_factory=list)


class ReportNarrativeDTO(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    executive_summary: str
    root_cause_analysis: str
    recommendations: list[str] = Field(default_factory=list)
    missing_data_warnings: list[str] = Field(default_factory=list)


class ReportDetailDTO(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: uuid.UUID
    title: str
    period_type: PeriodTypeEnum
    start_time: datetime
    end_time: datetime
    timezone: str = "Asia/Ho_Chi_Minh"
    dataset_ids: list[str] = Field(default_factory=list)
    metrics: ReportMetricsDTO
    narrative: ReportNarrativeDTO
    provenance_sources: list[dict[str, Any]] = Field(default_factory=list)
    created_at: datetime

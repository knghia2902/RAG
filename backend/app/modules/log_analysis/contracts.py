from typing import Optional
from pydantic import BaseModel, ConfigDict, Field
from app.modules.tickets.contracts import SystemEnum


class TimelineEventDTO(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    event_id: str
    timestamp: str
    system: SystemEnum
    event_name: str
    status: str
    is_failure_point: bool = False
    citation_id: Optional[int] = None
    source_filename: str
    line_number: Optional[int] = None
    raw_snippet: str


class CorrelatedOrderLogs(BaseModel):
    model_config = ConfigDict(extra="forbid")

    order_id: str
    total_events: int
    systems_involved: list[SystemEnum] = Field(default_factory=list)
    failure_point: Optional[TimelineEventDTO] = None
    timeline: list[TimelineEventDTO] = Field(default_factory=list)
    unparsed_logs_count: int = 0

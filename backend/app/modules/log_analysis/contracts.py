from enum import Enum
from typing import Any, Optional
from pydantic import BaseModel, ConfigDict, Field
from app.rag.contracts import EvidenceChunk
from app.modules.tickets.contracts import SystemEnum, SeverityEnum


class EvidenceKindEnum(str, Enum):
    CURRENT_LOG = "CURRENT_LOG"
    PRECEDENT_INCIDENT = "PRECEDENT_INCIDENT"
    SOP_PROCEDURE = "SOP_PROCEDURE"


class CategorizedEvidenceChunk(EvidenceChunk):
    evidence_kind: EvidenceKindEnum = EvidenceKindEnum.SOP_PROCEDURE


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


class IncidentClassificationDTO(BaseModel):
    model_config = ConfigDict(extra="forbid")

    error_group: str
    primary_system: SystemEnum
    suggested_priority: SeverityEnum
    confidence: float = Field(ge=0.0, le=1.0)


class RootCauseHypothesisDTO(BaseModel):
    model_config = ConfigDict(extra="forbid")

    hypothesis: str
    supporting_evidence_citations: list[int] = Field(default_factory=list)
    is_confirmed: bool = False
    confidence_level: str = "Trung bình"  # "Cao", "Trung bình", "Thấp"


class ActionStepDTO(BaseModel):
    model_config = ConfigDict(extra="forbid")

    step_number: int
    action: str
    sop_reference: str
    sop_citation_id: Optional[int] = None
    expected_outcome: str


class IncidentAnalysisResultDTO(BaseModel):
    model_config = ConfigDict(extra="forbid")

    order_id: str
    ticket_id: Optional[str] = None
    summary: str
    classification: IncidentClassificationDTO
    timeline: list[TimelineEventDTO] = Field(default_factory=list)
    hypotheses: list[RootCauseHypothesisDTO] = Field(default_factory=list)
    missing_information: list[str] = Field(default_factory=list)
    recommended_actions: list[ActionStepDTO] = Field(default_factory=list)
    citations: list[dict[str, Any]] = Field(default_factory=list)

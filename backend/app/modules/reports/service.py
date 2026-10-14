from datetime import date, datetime
from typing import Any, Optional
import uuid

from app.modules.reports.aggregator import (
    compute_period_bounds,
    aggregate_report_metrics,
)
from app.modules.reports.contracts import (
    PeriodTypeEnum,
    ReportFilterDTO,
    ReportMetricsDTO,
)


class ReportService:
    @staticmethod
    def get_period_bounds(
        period_type: PeriodTypeEnum,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        now: Optional[datetime] = None,
    ) -> tuple[datetime, datetime]:
        return compute_period_bounds(period_type, start_date, end_date, now)

    @staticmethod
    def compute_metrics(
        incident_analyses: list[Any],
        canonical_records: list[Any],
    ) -> ReportMetricsDTO:
        return aggregate_report_metrics(incident_analyses, canonical_records)

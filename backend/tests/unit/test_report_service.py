import uuid
from datetime import date, datetime, timezone
import pytest
from pydantic import ValidationError

from app.modules.reports.aggregator import (
    VN_TZ,
    compute_period_bounds,
    aggregate_report_metrics,
)
from app.modules.reports.contracts import (
    PeriodTypeEnum,
    ReportFilterDTO,
    ReportMetricsDTO,
)
from app.modules.reports.service import ReportService


def test_filter_dto_validation():
    # Valid custom dates
    valid = ReportFilterDTO(
        period_type=PeriodTypeEnum.CUSTOM,
        start_date=date(2026, 10, 1),
        end_date=date(2026, 10, 14),
    )
    assert valid.period_type == PeriodTypeEnum.CUSTOM

    # Invalid: start_date > end_date
    with pytest.raises(ValidationError):
        ReportFilterDTO(
            period_type=PeriodTypeEnum.CUSTOM,
            start_date=date(2026, 10, 14),
            end_date=date(2026, 10, 10),
        )

    # Invalid: missing dates for custom
    with pytest.raises(ValidationError):
        ReportFilterDTO(
            period_type=PeriodTypeEnum.CUSTOM,
            start_date=None,
            end_date=None,
        )

    # Invalid: range > 366 days
    with pytest.raises(ValidationError):
        ReportFilterDTO(
            period_type=PeriodTypeEnum.CUSTOM,
            start_date=date(2025, 1, 1),
            end_date=date(2026, 2, 1),
        )


def test_compute_period_bounds_daily():
    # Fixed point in time: 2026-10-14 15:30:00 UTC+7
    fixed_now = datetime(2026, 10, 14, 15, 30, 0, tzinfo=VN_TZ)
    start_utc, end_utc = compute_period_bounds(PeriodTypeEnum.DAILY, now=fixed_now)

    # In VN (UTC+7): 2026-10-14 00:00:00 to 2026-10-14 23:59:59.999999
    # In UTC: 2026-10-13 17:00:00 to 2026-10-14 16:59:59.999999
    assert start_utc.tzinfo == timezone.utc
    assert end_utc.tzinfo == timezone.utc

    assert start_utc == datetime(2026, 10, 13, 17, 0, 0, tzinfo=timezone.utc)
    assert end_utc == datetime(2026, 10, 14, 16, 59, 59, 999999, tzinfo=timezone.utc)


def test_compute_period_bounds_weekly_and_monthly():
    # Fixed point: Wednesday, 2026-10-14
    fixed_now = datetime(2026, 10, 14, 10, 0, 0, tzinfo=VN_TZ)

    # Weekly: Monday 2026-10-12 00:00:00 VN to Sunday 2026-10-18 23:59:59.999999 VN
    start_w_utc, end_w_utc = compute_period_bounds(PeriodTypeEnum.WEEKLY, now=fixed_now)
    assert start_w_utc == datetime(2026, 10, 11, 17, 0, 0, tzinfo=timezone.utc)
    assert end_w_utc == datetime(2026, 10, 18, 16, 59, 59, 999999, tzinfo=timezone.utc)

    # Monthly: 2026-10-01 00:00:00 VN to 2026-10-31 23:59:59.999999 VN
    start_m_utc, end_m_utc = compute_period_bounds(PeriodTypeEnum.MONTHLY, now=fixed_now)
    assert start_m_utc == datetime(2026, 9, 30, 17, 0, 0, tzinfo=timezone.utc)
    assert end_m_utc == datetime(2026, 10, 31, 16, 59, 59, 999999, tzinfo=timezone.utc)


def test_compute_period_bounds_custom():
    s_date = date(2026, 5, 1)
    e_date = date(2026, 5, 5)

    start_c_utc, end_c_utc = compute_period_bounds(
        PeriodTypeEnum.CUSTOM,
        start_date=s_date,
        end_date=e_date,
    )
    assert start_c_utc == datetime(2026, 4, 30, 17, 0, 0, tzinfo=timezone.utc)
    assert end_c_utc == datetime(2026, 5, 5, 16, 59, 59, 999999, tzinfo=timezone.utc)


def test_aggregate_deterministic_metrics():
    incidents = [
        {
            "id": uuid.uuid4(),
            "order_id": "DH001",
            "ticket_id": "TK-100",
            "classification_json": {
                "primary_system": "API_GATEWAY",
                "error_group": "504_GATEWAY_TIMEOUT",
                "suggested_priority": "P1",
                "status": "RESOLVED",
                "duration_minutes": 45,
            },
            "analysis_json": {},
        },
        {
            "id": uuid.uuid4(),
            "order_id": "DH002",
            "ticket_id": None,
            "classification_json": {
                "primary_system": "WMS",
                "error_group": "INVENTORY_MISMATCH",
                "suggested_priority": "P2",
                "status": "TIMEOUT",
            },
            "analysis_json": {},
        },
    ]

    canonical_records = [
        {
            "id": uuid.uuid4(),
            "record_metadata": {
                "record_type": "ticket",
                "ticket_id": "TK-100",
                "system": "API_GATEWAY",
                "priority": "P1",
                "status": "resolved",
                "duration_minutes": 45,
            },
        },
        {
            "id": uuid.uuid4(),
            "record_metadata": {
                "record_type": "ticket",
                "ticket_id": "TK-101",
                "system": "TMS",
                "priority": "P3",
                "status": "open",
            },
        },
    ]

    metrics = ReportService.compute_metrics(incidents, canonical_records)

    assert metrics.total_incidents == 2
    assert metrics.total_tickets == 2  # TK-100 and TK-101
    assert metrics.resolved_incidents == 1
    assert metrics.open_incidents == 1
    assert metrics.mttr_minutes == 45.0

    # System breakdown
    systems = {s.system: s for s in metrics.system_breakdown}
    assert "API_GATEWAY" in systems
    assert systems["API_GATEWAY"].incident_count == 1
    assert systems["API_GATEWAY"].ticket_count == 1

    assert "WMS" in systems
    assert systems["WMS"].incident_count == 1
    assert systems["WMS"].ticket_count == 0

    assert "TMS" in systems
    assert systems["TMS"].incident_count == 0
    assert systems["TMS"].ticket_count == 1


def test_mttr_calculation_only_for_resolved():
    incidents = [
        {
            "id": uuid.uuid4(),
            "order_id": "DH003",
            "classification_json": {
                "primary_system": "WMS",
                "error_group": "TIMEOUT",
                "suggested_priority": "P2",
                "status": "ERROR",  # Unresolved
                "duration_minutes": 999,  # Should NOT be included
            },
            "analysis_json": {},
        },
        {
            "id": uuid.uuid4(),
            "order_id": "DH004",
            "classification_json": {
                "primary_system": "WMS",
                "error_group": "TIMEOUT",
                "suggested_priority": "P2",
                "status": "PENDING",  # Unresolved
            },
            "analysis_json": {},
        },
    ]

    metrics = aggregate_report_metrics(incidents, [])
    assert metrics.resolved_incidents == 0
    assert metrics.open_incidents == 2
    assert metrics.mttr_minutes is None  # REP-03: No resolved incidents -> None


def test_recurring_error_grouping_rule():
    incidents = [
        {
            "id": uuid.uuid4(),
            "order_id": "DH001",
            "classification_json": {
                "primary_system": "API_GATEWAY",
                "error_group": "504_TIMEOUT",
                "suggested_priority": "P1",
            },
        },
        {
            "id": uuid.uuid4(),
            "order_id": "DH002",
            "classification_json": {
                "primary_system": "API_GATEWAY",
                "error_group": "504_TIMEOUT",
                "suggested_priority": "P1",
            },
        },
        {
            "id": uuid.uuid4(),
            "order_id": "DH003",
            "classification_json": {
                "primary_system": "WMS",
                "error_group": "BARCODE_SCAN_FAIL",
                "suggested_priority": "P3",
            },
        },
    ]

    metrics = aggregate_report_metrics(incidents, [])
    assert len(metrics.recurring_errors) == 1
    rec = metrics.recurring_errors[0]
    assert rec.system == "API_GATEWAY"
    assert rec.error_group == "504_TIMEOUT"
    assert rec.occurrence_count == 2
    assert "DH001" in rec.affected_orders
    assert "DH002" in rec.affected_orders
    assert rec.percentage == 66.7

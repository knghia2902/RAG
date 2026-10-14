import calendar
from datetime import date, datetime, timedelta, timezone
from typing import Any, Optional
import zoneinfo

from app.modules.reports.contracts import (
    PeriodTypeEnum,
    PriorityDistributionDTO,
    RecurringErrorItemDTO,
    ReportMetricsDTO,
    SystemDistributionDTO,
)

VN_TZ = zoneinfo.ZoneInfo("Asia/Ho_Chi_Minh")


def compute_period_bounds(
    period_type: PeriodTypeEnum,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    now: Optional[datetime] = None,
) -> tuple[datetime, datetime]:
    """
    Computes start and end timestamps in UTC corresponding to local bounds in Asia/Ho_Chi_Minh (UTC+7).
    Guarantees coverage from 00:00:00 to 23:59:59.999999 local time.
    """
    if now is None:
        now = datetime.now(tz=VN_TZ)
    elif now.tzinfo is None:
        now = now.replace(tzinfo=VN_TZ)
    else:
        now = now.astimezone(VN_TZ)

    if period_type == PeriodTypeEnum.DAILY:
        cur_date = now.date()
        start_local = datetime(cur_date.year, cur_date.month, cur_date.day, 0, 0, 0, 0, tzinfo=VN_TZ)
        end_local = datetime(cur_date.year, cur_date.month, cur_date.day, 23, 59, 59, 999999, tzinfo=VN_TZ)

    elif period_type == PeriodTypeEnum.WEEKLY:
        # Monday of current week
        start_date_local = now.date() - timedelta(days=now.weekday())
        end_date_local = start_date_local + timedelta(days=6)
        start_local = datetime(start_date_local.year, start_date_local.month, start_date_local.day, 0, 0, 0, 0, tzinfo=VN_TZ)
        end_local = datetime(end_date_local.year, end_date_local.month, end_date_local.day, 23, 59, 59, 999999, tzinfo=VN_TZ)

    elif period_type == PeriodTypeEnum.MONTHLY:
        start_date_local = date(now.year, now.month, 1)
        _, last_day = calendar.monthrange(now.year, now.month)
        end_date_local = date(now.year, now.month, last_day)
        start_local = datetime(start_date_local.year, start_date_local.month, start_date_local.day, 0, 0, 0, 0, tzinfo=VN_TZ)
        end_local = datetime(end_date_local.year, end_date_local.month, end_date_local.day, 23, 59, 59, 999999, tzinfo=VN_TZ)

    elif period_type == PeriodTypeEnum.CUSTOM:
        if start_date is None or end_date is None:
            raise ValueError("start_date và end_date là bắt buộc khi chọn kỳ tùy chọn (custom)")
        start_local = datetime(start_date.year, start_date.month, start_date.day, 0, 0, 0, 0, tzinfo=VN_TZ)
        end_local = datetime(end_date.year, end_date.month, end_date.day, 23, 59, 59, 999999, tzinfo=VN_TZ)

    else:
        raise ValueError(f"Loại kỳ không hợp lệ: {period_type}")

    return start_local.astimezone(timezone.utc), end_local.astimezone(timezone.utc)


def _get_val(obj: Any, key: str, default: Any = None) -> Any:
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


def aggregate_report_metrics(
    incident_analyses: list[Any],
    canonical_records: list[Any],
) -> ReportMetricsDTO:
    """
    Computes 100% deterministic metrics from incident analyses and canonical records.
    Never relies on top-k retrieval or LLM speculation.
    """
    total_incidents = len(incident_analyses)

    # 1. Ticket count
    seen_tickets: set[str] = set()
    ticket_durations: list[float] = []

    for rec in canonical_records:
        meta = _get_val(rec, "record_metadata") or {}
        rec_type = meta.get("record_type")
        ticket_id = meta.get("ticket_id") or meta.get("ticket_code")

        if rec_type == "ticket" or ticket_id:
            tid = str(ticket_id or _get_val(rec, "id"))
            seen_tickets.add(tid)

            # Ticket MTTR
            t_status = str(meta.get("status") or "").lower()
            if t_status in ("resolved", "closed", "hoàn tất", "đã đóng"):
                dur = meta.get("duration_minutes")
                if dur is not None:
                    try:
                        ticket_durations.append(float(dur))
                    except (ValueError, TypeError):
                        pass

    for inc in incident_analyses:
        inc_tid = _get_val(inc, "ticket_id")
        if inc_tid:
            seen_tickets.add(str(inc_tid))

    total_tickets = len(seen_tickets)

    # 2. Incident Resolution & MTTR
    resolved_incidents = 0
    open_incidents = 0
    incident_durations: list[float] = []

    for inc in incident_analyses:
        classif = _get_val(inc, "classification_json") or {}
        analysis = _get_val(inc, "analysis_json") or {}

        status = str(classif.get("status") or analysis.get("status") or "").upper()
        is_resolved = classif.get("is_resolved")
        if is_resolved is None:
            is_resolved = analysis.get("is_resolved")

        if is_resolved is True or status in ("RESOLVED", "SUCCESS", "CLOSED"):
            resolved_incidents += 1
            dur = analysis.get("duration_minutes") or classif.get("duration_minutes")
            if dur is not None:
                try:
                    incident_durations.append(float(dur))
                except (ValueError, TypeError):
                    pass
        else:
            open_incidents += 1

    all_durations = ticket_durations + incident_durations
    mttr_minutes: Optional[float] = (
        round(sum(all_durations) / len(all_durations), 1) if all_durations else None
    )

    # 3. System Breakdown
    system_incidents: dict[str, int] = {}
    system_tickets: dict[str, int] = {}

    for inc in incident_analyses:
        classif = _get_val(inc, "classification_json") or {}
        sys_name = str(classif.get("primary_system") or "OTHER").upper()
        system_incidents[sys_name] = system_incidents.get(sys_name, 0) + 1

    for rec in canonical_records:
        meta = _get_val(rec, "record_metadata") or {}
        if meta.get("record_type") == "ticket" or meta.get("ticket_id"):
            sys_name = str(meta.get("system") or "OTHER").upper()
            system_tickets[sys_name] = system_tickets.get(sys_name, 0) + 1

    all_systems = sorted(list(set(system_incidents.keys()) | set(system_tickets.keys())))
    system_breakdown: list[SystemDistributionDTO] = []
    for sys in all_systems:
        inc_count = system_incidents.get(sys, 0)
        tkt_count = system_tickets.get(sys, 0)
        pct = round(inc_count / total_incidents * 100, 1) if total_incidents > 0 else 0.0
        system_breakdown.append(
            SystemDistributionDTO(
                system=sys,
                incident_count=inc_count,
                ticket_count=tkt_count,
                percentage=pct,
            )
        )

    # 4. Priority Breakdown
    priority_counts: dict[str, int] = {}
    for inc in incident_analyses:
        classif = _get_val(inc, "classification_json") or {}
        p = str(classif.get("suggested_priority") or "P3").upper()
        priority_counts[p] = priority_counts.get(p, 0) + 1

    for rec in canonical_records:
        meta = _get_val(rec, "record_metadata") or {}
        if meta.get("record_type") == "ticket" or meta.get("ticket_id"):
            p = str(meta.get("priority") or "").upper()
            if p:
                priority_counts[p] = priority_counts.get(p, 0) + 1

    standard_priorities = ["P1", "P2", "P3", "P4"]
    for p in priority_counts:
        if p not in standard_priorities:
            standard_priorities.append(p)

    total_priority_count = sum(priority_counts.values())
    priority_breakdown: list[PriorityDistributionDTO] = []
    for p in standard_priorities:
        cnt = priority_counts.get(p, 0)
        pct = round(cnt / total_priority_count * 100, 1) if total_priority_count > 0 else 0.0
        priority_breakdown.append(
            PriorityDistributionDTO(
                priority=p,
                count=cnt,
                percentage=pct,
            )
        )

    # 5. Error Group Breakdown & Recurring Errors
    error_group_breakdown: dict[str, int] = {}
    recurring_tracker: dict[tuple[str, str], list[str]] = {}

    for inc in incident_analyses:
        classif = _get_val(inc, "classification_json") or {}
        sys_name = str(classif.get("primary_system") or "OTHER").upper()
        eg = str(classif.get("error_group") or "UNKNOWN_ERROR")
        order_id = str(_get_val(inc, "order_id") or "")

        error_group_breakdown[eg] = error_group_breakdown.get(eg, 0) + 1
        key = (sys_name, eg)
        if key not in recurring_tracker:
            recurring_tracker[key] = []
        if order_id:
            recurring_tracker[key].append(order_id)

    recurring_errors: list[RecurringErrorItemDTO] = []
    for (sys, eg), orders in recurring_tracker.items():
        occ = len(orders)
        if occ >= 2:
            pct = round(occ / total_incidents * 100, 1) if total_incidents > 0 else 0.0
            distinct_orders = list(dict.fromkeys(orders))
            recurring_errors.append(
                RecurringErrorItemDTO(
                    system=sys,
                    error_group=eg,
                    occurrence_count=occ,
                    percentage=pct,
                    affected_orders=distinct_orders,
                    sample_message=f"{sys}: {eg}",
                )
            )

    recurring_errors.sort(key=lambda x: x.occurrence_count, reverse=True)

    return ReportMetricsDTO(
        total_incidents=total_incidents,
        total_tickets=total_tickets,
        resolved_incidents=resolved_incidents,
        open_incidents=open_incidents,
        mttr_minutes=mttr_minutes,
        system_breakdown=system_breakdown,
        priority_breakdown=priority_breakdown,
        error_group_breakdown=error_group_breakdown,
        recurring_errors=recurring_errors,
    )

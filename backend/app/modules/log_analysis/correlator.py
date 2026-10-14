import re
import uuid
from typing import Any, Optional
from datetime import timezone
from dateutil import parser as date_parser

from app.modules.tickets.contracts import SystemEnum
from app.modules.log_analysis.contracts import TimelineEventDTO, CorrelatedOrderLogs

TIMESTAMP_PATTERN = re.compile(
    r"(\d{4}-\d{2}-\d{2}[T\s]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:?\d{2})?)"
)


class CrossSystemLogCorrelator:
    """Engine correlating multi-system logistics logs (WMS, API Gateway, TMS) for an order."""

    def correlate_order(self, order_id: str, raw_records: list[dict[str, Any]]) -> CorrelatedOrderLogs:
        """Extract and correlate order events across systems.

        Args:
            order_id: Exact order identifier (e.g. 'DH001').
            raw_records: List of dictionaries with keys like 'text', 'filename', 'line'.

        Returns:
            CorrelatedOrderLogs with ordered events and detected failure point.
        """
        clean_order_id = order_id.strip()
        # Enforce exact match on order ID with word boundaries to avoid DH001 matching DH010 or DH0011
        exact_regex = re.compile(r"\b" + re.escape(clean_order_id) + r"\b", re.IGNORECASE)

        matching_events: list[TimelineEventDTO] = []
        unparsed_count = 0

        for record in raw_records:
            text = record.get("text", "")
            if not text or not exact_regex.search(text):
                continue

            event = self._parse_log_entry(record, text)
            if event:
                matching_events.append(event)
            else:
                unparsed_count += 1

        # Sort events chronologically by timestamp
        def sort_key(e: TimelineEventDTO) -> str:
            return e.timestamp

        matching_events.sort(key=sort_key)

        # Detect the earliest sync failure point
        failure_point: Optional[TimelineEventDTO] = None
        annotated_events: list[TimelineEventDTO] = []
        systems_seen: set[SystemEnum] = set()

        for idx, ev in enumerate(matching_events, start=1):
            is_failure = False
            if failure_point is None and self._is_failure_event(ev):
                is_failure = True

            annotated_ev = TimelineEventDTO(
                event_id=ev.event_id,
                timestamp=ev.timestamp,
                system=ev.system,
                event_name=ev.event_name,
                status=ev.status,
                is_failure_point=is_failure,
                citation_id=idx,
                source_filename=ev.source_filename,
                line_number=ev.line_number,
                raw_snippet=ev.raw_snippet,
            )
            annotated_events.append(annotated_ev)
            systems_seen.add(ev.system)

            if is_failure:
                failure_point = annotated_ev

        return CorrelatedOrderLogs(
            order_id=clean_order_id,
            total_events=len(annotated_events),
            systems_involved=sorted(list(systems_seen), key=lambda s: s.value),
            failure_point=failure_point,
            timeline=annotated_events,
            unparsed_logs_count=unparsed_count,
        )

    def _parse_log_entry(self, record: dict[str, Any], text: str) -> Optional[TimelineEventDTO]:
        """Parse raw log text into a normalized TimelineEventDTO."""
        filename = record.get("filename", "log.txt")
        line_no = record.get("line")

        # 1. Extract timestamp
        ts_match = TIMESTAMP_PATTERN.search(text)
        if ts_match:
            raw_ts = ts_match.group(1).replace(" ", "T")
            try:
                dt = date_parser.parse(raw_ts)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                iso_ts = dt.isoformat()
            except Exception:
                iso_ts = raw_ts
        else:
            iso_ts = "1970-01-01T00:00:00Z"

        # 2. Determine system
        system = self._detect_system(filename, text)

        # 3. Determine event name and status
        event_name, status = self._detect_event_and_status(text)

        return TimelineEventDTO(
            event_id=str(uuid.uuid4()),
            timestamp=iso_ts,
            system=system,
            event_name=event_name,
            status=status,
            is_failure_point=False,
            citation_id=None,
            source_filename=filename,
            line_number=line_no,
            raw_snippet=text.strip(),
        )

    def _detect_system(self, filename: str, text: str) -> SystemEnum:
        lower_fn = filename.lower()
        lower_text = text.lower()

        # 1. Prioritize explicit text keywords
        if "api_gateway" in lower_text or "gateway" in lower_text or "api gateway" in lower_text:
            return SystemEnum.API_GATEWAY
        if "tms" in lower_text or "dieu_phoi" in lower_text or "dispatch" in lower_text:
            return SystemEnum.TMS
        if "wms" in lower_text or "kho" in lower_text:
            return SystemEnum.WMS
        if "inventory" in lower_text:
            return SystemEnum.INVENTORY
        if "erp" in lower_text:
            return SystemEnum.ERP

        # 2. Fallback to filename patterns
        if "api_gateway" in lower_fn or "gateway" in lower_fn or "api" in lower_fn:
            return SystemEnum.API_GATEWAY
        if "tms" in lower_fn or "dieu_phoi" in lower_fn or "dispatch" in lower_fn:
            return SystemEnum.TMS
        if "wms" in lower_fn or "kho" in lower_fn:
            return SystemEnum.WMS
        if "inventory" in lower_fn:
            return SystemEnum.INVENTORY
        if "erp" in lower_fn:
            return SystemEnum.ERP
        return SystemEnum.OTHER


    def _detect_event_and_status(self, text: str) -> tuple[str, str]:
        upper_text = text.upper()
        event_name = "LOG_EVENT"
        status = "INFO"

        if "PACKED" in upper_text or "ĐÓNG GÓI" in upper_text:
            event_name = "ORDER_PACKED"
            status = "SUCCESS"
        elif "CREATED" in upper_text or "TẠO ĐƠN" in upper_text:
            event_name = "ORDER_CREATED"
            status = "SUCCESS"
        elif "504" in upper_text or "GATEWAY TIMEOUT" in upper_text:
            event_name = "TMS_SYNC_TIMEOUT"
            status = "TIMEOUT"
        elif "500" in upper_text or "INTERNAL SERVER ERROR" in upper_text:
            event_name = "INTERNAL_ERROR"
            status = "ERROR"
        elif "PENDING" in upper_text or "CHỜ" in upper_text:
            event_name = "DISPATCH_PENDING"
            status = "PENDING"
        elif "RECEIVED" in upper_text or "DISPATCH" in upper_text:
            event_name = "DISPATCH_ASSIGNED"
            status = "SUCCESS"
        elif "ERROR" in upper_text or "FAIL" in upper_text:
            event_name = "OPERATION_FAILED"
            status = "ERROR"

        return event_name, status

    def _is_failure_event(self, ev: TimelineEventDTO) -> bool:
        """Check if an event marks an operational failure or timeout."""
        if ev.status in ("TIMEOUT", "ERROR", "FATAL"):
            return True
        upper_snippet = ev.raw_snippet.upper()
        if "504" in upper_snippet or "TIMEOUT" in upper_snippet or "CONNECTION REFUSED" in upper_snippet or "ERROR" in upper_snippet:
            return True
        return False

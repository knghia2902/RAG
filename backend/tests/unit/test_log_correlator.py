import pytest
from app.modules.log_analysis.correlator import CrossSystemLogCorrelator
from app.modules.tickets.contracts import SystemEnum


@pytest.fixture
def correlator() -> CrossSystemLogCorrelator:
    return CrossSystemLogCorrelator()


def test_exact_disambiguation_dh001_vs_dh010(correlator: CrossSystemLogCorrelator):
    records = [
        {"text": "2026-10-14 08:10:00 [INFO] WMS order DH001 packed at Song Than", "filename": "wms_songthan.log", "line": 10},
        {"text": "2026-10-14 08:10:05 [INFO] WMS order DH010 packed at Song Than", "filename": "wms_songthan.log", "line": 11},
        {"text": "2026-10-14 08:10:10 [INFO] WMS order DH0011 packed at Song Than", "filename": "wms_songthan.log", "line": 12},
        {"text": "2026-10-14 08:11:00 [INFO] API Gateway received request for DH001", "filename": "api_gateway.log", "line": 50},
        {"text": "2026-10-14 08:12:00 [INFO] API Gateway received request for DH001_OLD", "filename": "api_gateway.log", "line": 55},
        {"text": "2026-10-14 08:15:00 [ERROR] API Gateway timeout 504 for order DH001", "filename": "api_gateway.log", "line": 60},
    ]

    res = correlator.correlate_order("DH001", records)

    assert res.order_id == "DH001"
    # DH001 should match lines 10, 50, 60 (total 3)
    # DH010, DH0011, DH001_OLD must NOT match
    assert res.total_events == 3
    for ev in res.timeline:
        assert "DH001" in ev.raw_snippet
        assert "DH010" not in ev.raw_snippet
        assert "DH0011" not in ev.raw_snippet
        assert "DH001_OLD" not in ev.raw_snippet


def test_multi_system_timeline_chronological_ordering(correlator: CrossSystemLogCorrelator):
    # Log entries provided in disordered / reversed time
    records = [
        {"text": "2026-10-14 08:20:00 [WARN] TMS driver pending assignment for DH001", "filename": "tms_dispatch.log", "line": 100},
        {"text": "2026-10-14 08:15:00 [INFO] WMS warehouse Song Than packed DH001", "filename": "wms_songthan.log", "line": 15},
        {"text": "2026-10-14 08:15:05 [ERROR] API Gateway POST /tms/dispatch DH001 504 Gateway Timeout", "filename": "api_gateway.log", "line": 80},
    ]

    res = correlator.correlate_order("DH001", records)

    assert res.total_events == 3
    # Chronological order: 08:15:00 -> 08:15:05 -> 08:20:00
    assert res.timeline[0].system == SystemEnum.WMS
    assert res.timeline[0].line_number == 15
    assert res.timeline[1].system == SystemEnum.API_GATEWAY
    assert res.timeline[1].line_number == 80
    assert res.timeline[2].system == SystemEnum.TMS
    assert res.timeline[2].line_number == 100

    # Citations should be sequential 1, 2, 3
    assert [ev.citation_id for ev in res.timeline] == [1, 2, 3]


def test_failure_point_isolation(correlator: CrossSystemLogCorrelator):
    records = [
        {"text": "2026-10-14 08:15:00 [INFO] WMS order DH001 packed", "filename": "wms.log", "line": 1},
        {"text": "2026-10-14 08:15:05 [ERROR] API Gateway forward DH001 timeout 504", "filename": "api_gateway.log", "line": 20},
        {"text": "2026-10-14 08:15:30 [ERROR] TMS dispatch retry DH001 failed", "filename": "tms.log", "line": 40},
    ]

    res = correlator.correlate_order("DH001", records)

    assert res.failure_point is not None
    assert res.failure_point.line_number == 20
    assert res.failure_point.system == SystemEnum.API_GATEWAY
    assert res.failure_point.is_failure_point is True

    # Earliest failure point should be the ONLY one marked with is_failure_point=True
    failure_flags = [ev.is_failure_point for ev in res.timeline]
    assert failure_flags == [False, True, False]


def test_successful_order_no_failure_point(correlator: CrossSystemLogCorrelator):
    records = [
        {"text": "2026-10-14 08:10:00 [INFO] WMS order DH010 packed", "filename": "wms.log", "line": 1},
        {"text": "2026-10-14 08:10:02 [INFO] API Gateway 200 OK forward DH010", "filename": "api.log", "line": 2},
        {"text": "2026-10-14 08:10:05 [INFO] TMS driver received dispatch DH010", "filename": "tms.log", "line": 3},
    ]

    res = correlator.correlate_order("DH010", records)

    assert res.total_events == 3
    assert res.failure_point is None
    assert all(not ev.is_failure_point for ev in res.timeline)

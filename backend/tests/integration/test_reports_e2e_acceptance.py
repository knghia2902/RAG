from uuid import uuid4
import pytest
from sqlalchemy import delete
from app.auth.passwords import hash_password
from app.database.models import (
    Account,
    CanonicalRecord,
    Dataset,
    DatasetGrant,
    ImportJob,
    IncidentAnalysis,
    ParseRun,
    Source,
    SourceVersion,
)
from tests.conftest import HEADERS, PASSWORD


@pytest.fixture
def eval03_logistics_fixture(db):
    tech = Account(
        username=f"tech_eval03_{uuid4().hex[:6]}",
        display_name="Kỹ thuật viên Vận hành EVAL-03",
        role="technician",
        password_hash=hash_password(PASSWORD),
    )
    dataset = Dataset(name=f"Dataset-Logistics-EVAL03-{uuid4().hex[:8]}")
    db.add_all([tech, dataset])
    db.flush()

    grant = DatasetGrant(account_id=tech.id, dataset_id=dataset.id)
    db.add(grant)
    db.flush()

    # Source: wms_songthan_orders.log
    src_wms = Source(dataset_id=dataset.id, logical_filename="wms_songthan_orders.log", profile_id="text_log")
    db.add(src_wms)
    db.flush()

    ver_wms = SourceVersion(
        source_id=src_wms.id,
        version_number=1,
        content_hash="hash_wms_eval03",
        storage_key="key_wms_eval03",
        size_bytes=500,
        mime_type="text/plain",
    )
    db.add(ver_wms)
    db.flush()
    src_wms.active_version_id = ver_wms.id

    job = ImportJob(source_version_id=ver_wms.id, state="ready")
    db.add(job)
    db.flush()

    run = ParseRun(
        source_version_id=ver_wms.id,
        job_id=job.id,
        parser_name="text_log",
        parser_version="1.0",
        status="published",
    )
    db.add(run)
    db.flush()

    # Add canonical ticket record (ground truth: 1 ticket)
    ticket_rec = CanonicalRecord(
        parse_run_id=run.id,
        source_version_id=ver_wms.id,
        dataset_id=dataset.id,
        position=1,
        locator_data={"line_start": 1, "line_end": 2},
        content_text="Ticket TK-EVAL-01: Lỗi timeout API Gateway DH001",
        record_metadata={
            "record_type": "ticket",
            "ticket_id": "TK-EVAL-01",
            "system": "API_GATEWAY",
            "priority": "P1",
            "status": "resolved",
            "duration_minutes": 30,
        },
    )
    db.add(ticket_rec)

    # Add 3 IncidentAnalyses (ground truth: 3 incidents, 2 resolved, 1 open)
    # DH001: P1, API_GATEWAY, 504_GATEWAY_TIMEOUT, RESOLVED, 40 min
    inc1 = IncidentAnalysis(
        account_id=tech.id,
        order_id="DH001",
        ticket_id="TK-EVAL-01",
        input_mode="quick_form",
        title="Sự cố đơn hàng DH001",
        classification_json={
            "primary_system": "API_GATEWAY",
            "error_group": "504_GATEWAY_TIMEOUT",
            "suggested_priority": "P1",
            "status": "RESOLVED",
            "duration_minutes": 40,
        },
        timeline_json=[],
        analysis_json={"summary": "Timeout kết nối API Gateway và WMS", "hypotheses": []},
        citations_json=[],
    )
    # DH010: P1, API_GATEWAY, 504_GATEWAY_TIMEOUT, RESOLVED, 20 min -> Recurring error!
    inc2 = IncidentAnalysis(
        account_id=tech.id,
        order_id="DH010",
        ticket_id=None,
        input_mode="quick_form",
        title="Sự cố đơn hàng DH010",
        classification_json={
            "primary_system": "API_GATEWAY",
            "error_group": "504_GATEWAY_TIMEOUT",
            "suggested_priority": "P1",
            "status": "RESOLVED",
            "duration_minutes": 20,
        },
        timeline_json=[],
        analysis_json={"summary": "Timeout kết nối API Gateway và TMS", "hypotheses": []},
        citations_json=[],
    )
    # DH002: P2, WMS, INVENTORY_MISMATCH, TIMEOUT (Open), duration should NOT be included in MTTR
    inc3 = IncidentAnalysis(
        account_id=tech.id,
        order_id="DH002",
        ticket_id=None,
        input_mode="quick_form",
        title="Sự cố đơn hàng DH002",
        classification_json={
            "primary_system": "WMS",
            "error_group": "INVENTORY_MISMATCH",
            "suggested_priority": "P2",
            "status": "TIMEOUT",
            "duration_minutes": 999,
        },
        timeline_json=[],
        analysis_json={"summary": "Lệch tồn kho chưa hoàn tất", "hypotheses": []},
        citations_json=[],
    )
    db.add_all([inc1, inc2, inc3])
    db.commit()

    return tech, dataset


def test_eval03_report_metrics_match_ground_truth(client, db, eval03_logistics_fixture):
    tech, dataset = eval03_logistics_fixture

    # Login
    login_res = client.post(
        "/api/v1/auth/login",
        json={"username": tech.username, "password": PASSWORD},
        headers=HEADERS,
    )
    assert login_res.status_code == 200
    csrf = login_res.json()["csrf_token"]
    h = {**HEADERS, "X-CSRF-Token": csrf}

    # Generate daily report
    res = client.post(
        "/api/v1/reports/generate",
        json={"period_type": "daily", "dataset_ids": [str(dataset.id)]},
        headers=h,
    )
    assert res.status_code == 200
    report_data = res.json()
    metrics = report_data["metrics"]

    # EVAL-03 Criterion 1: Total incidents & tickets match ground truth
    assert metrics["total_incidents"] == 3
    assert metrics["total_tickets"] == 1
    assert metrics["resolved_incidents"] == 2
    assert metrics["open_incidents"] == 1

    # EVAL-03 Criterion 2: MTTR only computed for resolved items
    # Durations of resolved items: ticket (30) + DH001 (40) + DH010 (20) = 90 / 3 = 30.0 min
    assert metrics["mttr_minutes"] == 30.0

    # EVAL-03 Criterion 3: Recurring error rule: [API_GATEWAY + 504_GATEWAY_TIMEOUT] >= 2 occurrences
    assert len(metrics["recurring_errors"]) == 1
    rec = metrics["recurring_errors"][0]
    assert rec["system"] == "API_GATEWAY"
    assert rec["error_group"] == "504_GATEWAY_TIMEOUT"
    assert rec["occurrence_count"] == 2
    assert "DH001" in rec["affected_orders"]
    assert "DH010" in rec["affected_orders"]
    assert rec["percentage"] == 66.7

    # EVAL-03 Criterion 4: Provenance metadata preserved
    assert len(report_data["provenance_sources"]) >= 1
    prov = report_data["provenance_sources"][0]
    assert prov["filename"] == "wms_songthan_orders.log"
    assert prov["dataset_id"] == str(dataset.id)


def test_eval03_pdf_download_and_scope_recheck_e2e(client, db, eval03_logistics_fixture):
    tech, dataset = eval03_logistics_fixture

    # Login
    login_res = client.post(
        "/api/v1/auth/login",
        json={"username": tech.username, "password": PASSWORD},
        headers=HEADERS,
    )
    csrf = login_res.json()["csrf_token"]
    h = {**HEADERS, "X-CSRF-Token": csrf}

    # Generate report
    gen_res = client.post(
        "/api/v1/reports/generate",
        json={"period_type": "daily", "dataset_ids": [str(dataset.id)]},
        headers=h,
    )
    assert gen_res.status_code == 200
    report_id = gen_res.json()["id"]

    # 1. Download valid Vietnamese PDF
    pdf_res = client.get(f"/api/v1/reports/{report_id}/pdf", headers=h)
    assert pdf_res.status_code == 200
    assert "application/pdf" in pdf_res.headers.get("content-type", "")
    assert pdf_res.content.startswith(b"%PDF-1.")
    assert len(pdf_res.content) > 1000

    # 2. Revoke Dataset permission from technician (simulating permission revocation)
    db.execute(
        delete(DatasetGrant).where(
            DatasetGrant.account_id == tech.id,
            DatasetGrant.dataset_id == dataset.id,
        )
    )
    db.commit()

    # 3. Live Scope Recheck: Calling detail endpoint MUST immediately return HTTP 403 Forbidden
    detail_res = client.get(f"/api/v1/reports/{report_id}", headers=h)
    assert detail_res.status_code == 403
    assert "thu hồi" in detail_res.json()["detail"].lower()

    # 4. Live Scope Recheck: Calling PDF endpoint MUST immediately return HTTP 403 Forbidden
    pdf_revoked_res = client.get(f"/api/v1/reports/{report_id}/pdf", headers=h)
    assert pdf_revoked_res.status_code == 403

    # 5. History listing excludes the revoked report
    hist_res = client.get("/api/v1/reports/history", headers=h)
    assert hist_res.status_code == 200
    ids = [item["id"] for item in hist_res.json()]
    assert report_id not in ids

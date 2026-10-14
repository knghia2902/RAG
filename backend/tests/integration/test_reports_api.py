import io
from uuid import uuid4
import pytest
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
def tech_with_report_fixtures(db):
    tech1 = Account(
        username=f"tech_rep1_{uuid4().hex[:6]}",
        display_name="Tech Report 1",
        role="technician",
        password_hash=hash_password(PASSWORD),
    )
    tech2 = Account(
        username=f"tech_rep2_{uuid4().hex[:6]}",
        display_name="Tech Report 2",
        role="technician",
        password_hash=hash_password(PASSWORD),
    )
    dataset1 = Dataset(name=f"Dataset-Reports-1-{uuid4().hex[:8]}")
    dataset2 = Dataset(name=f"Dataset-Reports-2-{uuid4().hex[:8]}")
    db.add_all([tech1, tech2, dataset1, dataset2])
    db.flush()

    db.add(DatasetGrant(account_id=tech1.id, dataset_id=dataset1.id))
    db.add(DatasetGrant(account_id=tech2.id, dataset_id=dataset2.id))
    db.flush()

    source = Source(dataset_id=dataset1.id, logical_filename="wms_logistics.log", profile_id="text_log")
    db.add(source)
    db.flush()

    version = SourceVersion(
        source_id=source.id,
        version_number=1,
        content_hash="rep_hash_1",
        storage_key="rep_key_1",
        size_bytes=400,
        mime_type="text/plain",
    )
    db.add(version)
    db.flush()
    source.active_version_id = version.id

    job = ImportJob(source_version_id=version.id, state="ready")
    db.add(job)
    db.flush()

    run = ParseRun(
        source_version_id=version.id,
        job_id=job.id,
        parser_name="text_log",
        parser_version="1.0",
        status="published",
    )
    db.add(run)
    db.flush()

    # Add canonical ticket records
    rec_ticket = CanonicalRecord(
        parse_run_id=run.id,
        source_version_id=version.id,
        dataset_id=dataset1.id,
        position=1,
        locator_data={"line": 1},
        content_text="Ticket TK-888: WMS connection error",
        record_metadata={
            "record_type": "ticket",
            "ticket_id": "TK-888",
            "system": "WMS",
            "priority": "P2",
            "status": "resolved",
            "duration_minutes": 30,
        },
    )
    db.add(rec_ticket)

    # Add IncidentAnalysis records
    inc1 = IncidentAnalysis(
        account_id=tech1.id,
        order_id="DH001",
        ticket_id="TK-888",
        input_mode="quick_form",
        title="Phân tích sự cố DH001",
        classification_json={
            "primary_system": "API_GATEWAY",
            "error_group": "504_GATEWAY_TIMEOUT",
            "suggested_priority": "P1",
            "status": "RESOLVED",
            "duration_minutes": 25,
        },
        timeline_json=[],
        analysis_json={
            "summary": "Timeout kết nối API Gateway",
            "hypotheses": [],
            "missing_information": [],
            "recommended_actions": [],
        },
        citations_json=[],
    )
    inc2 = IncidentAnalysis(
        account_id=tech1.id,
        order_id="DH002",
        ticket_id=None,
        input_mode="quick_form",
        title="Phân tích sự cố DH002",
        classification_json={
            "primary_system": "API_GATEWAY",
            "error_group": "504_GATEWAY_TIMEOUT",
            "suggested_priority": "P1",
            "status": "TIMEOUT",
        },
        timeline_json=[],
        analysis_json={
            "summary": "Lỗi lặp lại API Gateway timeout",
            "hypotheses": [],
            "missing_information": [],
            "recommended_actions": [],
        },
        citations_json=[],
    )
    db.add_all([inc1, inc2])
    db.commit()

    return tech1, tech2, dataset1, dataset2


def test_generate_report_endpoint(client, db, tech_with_report_fixtures):
    tech1, _, dataset1, _ = tech_with_report_fixtures

    # Login as tech1
    login_res = client.post(
        "/api/v1/auth/login",
        json={"username": tech1.username, "password": PASSWORD},
        headers=HEADERS,
    )
    assert login_res.status_code == 200
    csrf = login_res.json()["csrf_token"]
    h = {**HEADERS, "X-CSRF-Token": csrf}

    # Generate daily report
    res = client.post(
        "/api/v1/reports/generate",
        json={"period_type": "daily", "dataset_ids": [str(dataset1.id)]},
        headers=h,
    )
    assert res.status_code == 200
    data = res.json()

    assert data["period_type"] == "daily"
    assert "metrics" in data
    assert data["metrics"]["total_incidents"] == 2
    assert data["metrics"]["total_tickets"] == 1
    assert data["metrics"]["resolved_incidents"] == 1
    assert data["metrics"]["open_incidents"] == 1
    assert data["metrics"]["mttr_minutes"] is not None

    # Recurring error check
    assert len(data["metrics"]["recurring_errors"]) >= 1
    rec = data["metrics"]["recurring_errors"][0]
    assert rec["system"] == "API_GATEWAY"
    assert rec["error_group"] == "504_GATEWAY_TIMEOUT"
    assert rec["occurrence_count"] == 2

    # Narrative and provenance checks
    assert "narrative" in data
    assert "executive_summary" in data["narrative"]
    assert "root_cause_analysis" in data["narrative"]
    assert "provenance_sources" in data
    assert len(data["provenance_sources"]) >= 1


def test_report_history_and_idor_protection(client, db, tech_with_report_fixtures):
    tech1, tech2, dataset1, _ = tech_with_report_fixtures

    # Tech 1 logs in and creates report
    res1 = client.post("/api/v1/auth/login", json={"username": tech1.username, "password": PASSWORD}, headers=HEADERS)
    h1 = {**HEADERS, "X-CSRF-Token": res1.json()["csrf_token"]}

    rep_res = client.post(
        "/api/v1/reports/generate",
        json={"period_type": "daily", "dataset_ids": [str(dataset1.id)]},
        headers=h1,
    )
    assert rep_res.status_code == 200
    report_id = rep_res.json()["id"]

    # Tech 1 lists history -> sees the report
    hist1 = client.get("/api/v1/reports/history", headers=h1)
    assert hist1.status_code == 200
    ids = [item["id"] for item in hist1.json()]
    assert report_id in ids

    # Tech 2 logs in
    res2 = client.post("/api/v1/auth/login", json={"username": tech2.username, "password": PASSWORD}, headers=HEADERS)
    h2 = {**HEADERS, "X-CSRF-Token": res2.json()["csrf_token"]}

    # Tech 2 lists history -> cannot see Tech 1's report
    hist2 = client.get("/api/v1/reports/history", headers=h2)
    assert hist2.status_code == 200
    ids2 = [item["id"] for item in hist2.json()]
    assert report_id not in ids2

    # Tech 2 tries to access Tech 1's report directly (IDOR attempt)
    detail_idor = client.get(f"/api/v1/reports/{report_id}", headers=h2)
    assert detail_idor.status_code == 403

    # Tech 2 tries to download PDF of Tech 1's report
    pdf_idor = client.get(f"/api/v1/reports/{report_id}/pdf", headers=h2)
    assert pdf_idor.status_code == 403


def test_download_pdf_endpoint(client, db, tech_with_report_fixtures):
    tech1, _, dataset1, _ = tech_with_report_fixtures

    res1 = client.post("/api/v1/auth/login", json={"username": tech1.username, "password": PASSWORD}, headers=HEADERS)
    h1 = {**HEADERS, "X-CSRF-Token": res1.json()["csrf_token"]}

    rep_res = client.post(
        "/api/v1/reports/generate",
        json={"period_type": "daily", "dataset_ids": [str(dataset1.id)]},
        headers=h1,
    )
    report_id = rep_res.json()["id"]

    pdf_res = client.get(f"/api/v1/reports/{report_id}/pdf", headers=h1)
    assert pdf_res.status_code == 200
    assert "application/pdf" in pdf_res.headers.get("content-type", "")
    assert pdf_res.content.startswith(b"%PDF-1.")
    assert len(pdf_res.content) > 1000


def test_report_provenance_endpoint(client, db, tech_with_report_fixtures):
    tech1, _, dataset1, _ = tech_with_report_fixtures

    res1 = client.post("/api/v1/auth/login", json={"username": tech1.username, "password": PASSWORD}, headers=HEADERS)
    h1 = {**HEADERS, "X-CSRF-Token": res1.json()["csrf_token"]}

    rep_res = client.post(
        "/api/v1/reports/generate",
        json={"period_type": "daily", "dataset_ids": [str(dataset1.id)]},
        headers=h1,
    )
    report_id = rep_res.json()["id"]

    prov_res = client.get(f"/api/v1/reports/{report_id}/provenance", headers=h1)
    assert prov_res.status_code == 200
    prov_data = prov_res.json()
    assert isinstance(prov_data, list)
    assert len(prov_data) >= 1
    assert any(p.get("dataset_id") == str(dataset1.id) for p in prov_data)

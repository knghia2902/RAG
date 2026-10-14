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
    ParseRun,
    Source,
    SourceVersion,
)
from tests.conftest import HEADERS, PASSWORD


@pytest.fixture
def tech_with_logistics_data(db):
    tech = Account(
        username=f"tech_inc_{uuid4().hex[:6]}",
        display_name="Tech Incident",
        role="technician",
        password_hash=hash_password(PASSWORD),
    )
    dataset = Dataset(name=f"Dataset-Logistics-{uuid4().hex[:8]}")
    db.add_all([tech, dataset])
    db.flush()

    grant = DatasetGrant(account_id=tech.id, dataset_id=dataset.id)
    db.add(grant)
    db.flush()

    source = Source(dataset_id=dataset.id, logical_filename="wms_gateway.log", profile_id="text_log")
    db.add(source)
    db.flush()

    version = SourceVersion(
        source_id=source.id,
        version_number=1,
        content_hash="hash_inc_1",
        storage_key="key_inc_1",
        size_bytes=300,
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

    r1 = CanonicalRecord(
        parse_run_id=run.id,
        source_version_id=version.id,
        dataset_id=dataset.id,
        position=1,
        locator_data={"line_start": 1, "line_end": 2},
        content_text="2026-10-14 08:15:00 [INFO] WMS order DH001 packed at warehouse Song Than",
    )
    r2 = CanonicalRecord(
        parse_run_id=run.id,
        source_version_id=version.id,
        dataset_id=dataset.id,
        position=2,
        locator_data={"line_start": 3, "line_end": 4},
        content_text="2026-10-14 08:15:05 [ERROR] API Gateway forward DH001 to TMS timeout 504 Gateway Timeout",
    )
    db.add_all([r1, r2])
    db.commit()

    return tech, dataset, source


def test_analyze_order_endpoint(client, db, tech_with_logistics_data):
    tech, dataset, source = tech_with_logistics_data

    # Login
    login_res = client.post(
        "/api/v1/auth/login",
        json={"username": tech.username, "password": PASSWORD},
        headers=HEADERS,
    )
    assert login_res.status_code == 200
    csrf = login_res.json()["csrf_token"]
    h = {**HEADERS, "X-CSRF-Token": csrf}

    # Analyze order DH001
    res = client.post(
        "/api/v1/incidents/analyze",
        json={"order_id": "DH001", "description": "Lỗi đồng bộ WMS TMS"},
        headers=h,
    )
    assert res.status_code == 200
    data = res.json()

    assert data["order_id"] == "DH001"
    assert "classification" in data
    assert data["classification"]["primary_system"] == "API_GATEWAY"
    assert "timeline" in data
    assert len(data["timeline"]) == 2
    assert "hypotheses" in data
    assert len(data["hypotheses"]) >= 1
    assert "recommended_actions" in data
    assert len(data["recommended_actions"]) >= 1
    assert "missing_information" in data
    assert "citations" in data


def test_upload_valid_ticket_json_and_csv(client, db, tech_with_logistics_data):
    tech, _, _ = tech_with_logistics_data

    login_res = client.post(
        "/api/v1/auth/login",
        json={"username": tech.username, "password": PASSWORD},
        headers=HEADERS,
    )
    csrf = login_res.json()["csrf_token"]
    upload_headers = {
        "Origin": HEADERS["Origin"],
        "X-Requested-With": HEADERS["X-Requested-With"],
        "X-CSRF-Token": csrf,
    }

    # Upload JSON
    valid_json = b"""[
      {
        "ticket_id": "TCK-001",
        "order_id": "DH001",
        "timestamp": "2026-10-14T08:15:00Z",
        "system": "WMS",
        "severity": "P1",
        "description": "Don hang DH001 khong dong bo duoc sang TMS"
      }
    ]"""
    res_json = client.post(
        "/api/v1/incidents/upload-ticket",
        files={"file": ("tickets.json", io.BytesIO(valid_json), "application/json")},
        headers=upload_headers,
    )
    assert res_json.status_code == 200
    assert "Tiếp nhận thành công" in res_json.json()["message"]
    assert res_json.json()["total_tickets"] == 1

    # Upload CSV
    valid_csv = b"""ticket_id,order_id,timestamp,system,severity,description
TCK-002,DH001,2026-10-14T08:20:00Z,TMS,P2,Don hang DH001 bi cham gio giao
"""
    res_csv = client.post(
        "/api/v1/incidents/upload-ticket",
        files={"file": ("tickets.csv", io.BytesIO(valid_csv), "text/csv")},
        headers=upload_headers,
    )
    assert res_csv.status_code == 200
    assert "Tiếp nhận thành công" in res_csv.json()["message"]


def test_upload_invalid_ticket_schema_422(client, db, tech_with_logistics_data):
    tech, _, _ = tech_with_logistics_data

    login_res = client.post(
        "/api/v1/auth/login",
        json={"username": tech.username, "password": PASSWORD},
        headers=HEADERS,
    )
    csrf = login_res.json()["csrf_token"]
    upload_headers = {
        "Origin": HEADERS["Origin"],
        "X-Requested-With": HEADERS["X-Requested-With"],
        "X-CSRF-Token": csrf,
    }

    # Missing required header 'severity'
    invalid_csv = b"""ticket_id,order_id,timestamp,system,description
TCK-003,DH001,2026-10-14T08:20:00Z,TMS,Mo ta ngan
"""
    res = client.post(
        "/api/v1/incidents/upload-ticket",
        files={"file": ("invalid.csv", io.BytesIO(invalid_csv), "text/csv")},
        headers=upload_headers,
    )
    assert res.status_code == 422
    data = res.json()
    assert "detail" in data
    assert "errors" in data["detail"]


def test_incident_history(client, db, tech_with_logistics_data):
    tech, _, _ = tech_with_logistics_data

    login_res = client.post(
        "/api/v1/auth/login",
        json={"username": tech.username, "password": PASSWORD},
        headers=HEADERS,
    )
    h = {**HEADERS, "X-CSRF-Token": login_res.json()["csrf_token"]}

    # Perform analysis
    client.post(
        "/api/v1/incidents/analyze",
        json={"order_id": "DH001"},
        headers=h,
    )

    # Fetch history
    hist_res = client.get("/api/v1/incidents/history", headers=h)
    assert hist_res.status_code == 200
    items = hist_res.json()
    assert len(items) >= 1
    assert any(item["order_id"] == "DH001" for item in items)

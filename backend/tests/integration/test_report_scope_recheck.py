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
def tech_with_scoped_report(db):
    tech = Account(
        username=f"tech_scope_{uuid4().hex[:6]}",
        display_name="Tech Scope Recheck",
        role="technician",
        password_hash=hash_password(PASSWORD),
    )
    dataset = Dataset(name=f"Dataset-Scoped-{uuid4().hex[:8]}")
    db.add_all([tech, dataset])
    db.flush()

    grant = DatasetGrant(account_id=tech.id, dataset_id=dataset.id)
    db.add(grant)
    db.flush()

    source = Source(dataset_id=dataset.id, logical_filename="scope_test.log", profile_id="text_log")
    db.add(source)
    db.flush()

    version = SourceVersion(
        source_id=source.id,
        version_number=1,
        content_hash="scope_hash",
        storage_key="scope_key",
        size_bytes=200,
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

    inc = IncidentAnalysis(
        account_id=tech.id,
        order_id="DH999",
        ticket_id="TK-999",
        input_mode="quick_form",
        title="Sự cố kiểm thử scope",
        classification_json={
            "primary_system": "WMS",
            "error_group": "INVENTORY_ERROR",
            "suggested_priority": "P2",
            "status": "RESOLVED",
            "duration_minutes": 15,
        },
        timeline_json=[],
        analysis_json={
            "summary": "Kiểm thử phạm vi quyền",
            "hypotheses": [],
            "missing_information": [],
            "recommended_actions": [],
        },
        citations_json=[],
    )
    db.add(inc)
    db.commit()

    return tech, dataset


def test_live_scope_recheck_revocation_denied(client, db, tech_with_scoped_report):
    tech, dataset = tech_with_scoped_report

    # 1. Login as technician
    login_res = client.post(
        "/api/v1/auth/login",
        json={"username": tech.username, "password": PASSWORD},
        headers=HEADERS,
    )
    assert login_res.status_code == 200
    csrf = login_res.json()["csrf_token"]
    h = {**HEADERS, "X-CSRF-Token": csrf}

    # 2. Generate report while technician has access to dataset
    gen_res = client.post(
        "/api/v1/reports/generate",
        json={"period_type": "daily", "dataset_ids": [str(dataset.id)]},
        headers=h,
    )
    assert gen_res.status_code == 200
    report_id = gen_res.json()["id"]

    # 3. Verify detail and PDF can be accessed before revocation
    detail_ok = client.get(f"/api/v1/reports/{report_id}", headers=h)
    assert detail_ok.status_code == 200

    pdf_ok = client.get(f"/api/v1/reports/{report_id}/pdf", headers=h)
    assert pdf_ok.status_code == 200

    # 4. Revoke dataset permission: Delete DatasetGrant record (simulating Admin action)
    db.execute(
        delete(DatasetGrant).where(
            DatasetGrant.account_id == tech.id,
            DatasetGrant.dataset_id == dataset.id,
        )
    )
    db.commit()

    # 5. Live Scope Recheck: Calling detail endpoint MUST immediately return HTTP 403 Forbidden (AUTH-04, REP-06)
    detail_denied = client.get(f"/api/v1/reports/{report_id}", headers=h)
    assert detail_denied.status_code == 403
    assert "thu hồi" in detail_denied.json()["detail"].lower()

    # 6. Live Scope Recheck: Calling PDF download endpoint MUST immediately return HTTP 403 Forbidden (AUTH-04, REP-06)
    pdf_denied = client.get(f"/api/v1/reports/{report_id}/pdf", headers=h)
    assert pdf_denied.status_code == 403

    # 7. Calling history endpoint should not list the report after access revocation
    hist_res = client.get("/api/v1/reports/history", headers=h)
    assert hist_res.status_code == 200
    returned_ids = [item["id"] for item in hist_res.json()]
    assert report_id not in returned_ids

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


def test_live_scope_recheck_revocation_denied(client, db):
    """Xác minh AUTH-04 & D-05: Khi quyền truy cập Dataset bị thu hồi,

    cả endpoint xem chi tiết sự cố lẫn xem trước trích dẫn đều bị từ chối với 403 Forbidden.
    """
    # 1. Khởi tạo Tech và Dataset A
    tech = Account(
        username=f"tech_scope_{uuid4().hex[:6]}",
        display_name="Tech Scope Check",
        role="technician",
        password_hash=hash_password(PASSWORD),
    )
    dataset = Dataset(name=f"Dataset-Scope-{uuid4().hex[:8]}")
    db.add_all([tech, dataset])
    db.flush()

    grant = DatasetGrant(account_id=tech.id, dataset_id=dataset.id)
    db.add(grant)
    db.flush()

    # Nạp Source và Record log của DH001
    src = Source(dataset_id=dataset.id, logical_filename="wms_desync.log", profile_id="text_log")
    db.add(src)
    db.flush()
    ver = SourceVersion(
        source_id=src.id,
        version_number=1,
        content_hash="hscope",
        storage_key="kscope",
        size_bytes=200,
        mime_type="text/plain",
    )
    db.add(ver)
    db.flush()
    src.active_version_id = ver.id

    job = ImportJob(source_version_id=ver.id, state="ready")
    db.add(job)
    db.flush()
    run = ParseRun(
        source_version_id=ver.id,
        job_id=job.id,
        parser_name="text_log",
        parser_version="1.0",
        status="published",
    )
    db.add(run)
    db.flush()

    rec = CanonicalRecord(
        parse_run_id=run.id,
        source_version_id=ver.id,
        dataset_id=dataset.id,
        position=1,
        locator_data={"line_start": 10, "line_end": 12},
        content_text="2026-10-14 08:15:05 [ERROR] API Gateway forward DH001 to TMS timeout 504 Gateway Timeout",
    )
    db.add(rec)
    db.commit()

    # 2. Tech đăng nhập
    login_res = client.post(
        "/api/v1/auth/login",
        json={"username": tech.username, "password": PASSWORD},
        headers=HEADERS,
    )
    assert login_res.status_code == 200
    h = {**HEADERS, "X-CSRF-Token": login_res.json()["csrf_token"]}

    # 3. Phân tích sự cố thành công khi còn quyền
    analyze_res = client.post(
        "/api/v1/incidents/analyze",
        json={"order_id": "DH001"},
        headers=h,
    )
    assert analyze_res.status_code == 200
    analysis_id = analyze_res.json()["id"]

    # Kiểm tra xem chi tiết ca phân tích thành công (200 OK)
    detail_res = client.get(f"/api/v1/incidents/{analysis_id}", headers=h)
    assert detail_res.status_code == 200

    # Kiểm tra xem preview trích dẫn thành công (200 OK)
    prev_url = f"/api/v1/incidents/citations/1/preview?dataset_id={dataset.id}&source_id={src.id}&line=10"
    prev_res = client.get(prev_url, headers=h)
    assert prev_res.status_code == 200
    assert "timeout 504" in prev_res.json()["excerpt_text"]

    # 4. Thu hồi quyền Dataset của Kỹ thuật viên
    db.delete(grant)
    db.commit()

    # 5. Live Scope Recheck (D-05, AUTH-04): Xem lại chi tiết sự cố -> BỊ TỪ CHỐI 403
    detail_denied = client.get(f"/api/v1/incidents/{analysis_id}", headers=h)
    assert detail_denied.status_code == 403
    assert "thu hồi" in detail_denied.json()["detail"]

    # 6. Live Scope Recheck: Click mở trích dẫn -> BỊ TỪ CHỐI 403
    prev_denied = client.get(prev_url, headers=h)
    assert prev_denied.status_code == 403
    assert "thu hồi" in prev_denied.json()["detail"]

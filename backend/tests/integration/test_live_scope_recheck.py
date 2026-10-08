from uuid import uuid4
import pytest
from app.auth.passwords import hash_password
from app.database.models import (
    Account,
    CanonicalRecord,
    ChatMessage,
    ChatSession,
    Dataset,
    DatasetGrant,
    ImportJob,
    ParseRun,
    Source,
    SourceVersion,
)
from tests.conftest import HEADERS, PASSWORD


def test_live_scope_recheck_revocation_denies_citation_preview(client, db):
    """Xác minh D-05 & T-03-10: Khi quyền Dataset bị thu hồi giữa chừng,

    preview citation bị chặn ngay lập tức với 403 Forbidden.
    """
    # 1. Tạo Tech và Dataset
    tech = Account(username="tech_recheck", display_name="Tech Recheck", role="technician", password_hash=hash_password(PASSWORD))
    dataset = Dataset(name=f"Dataset-Recheck-{uuid4().hex[:8]}")
    db.add_all([tech, dataset])
    db.flush()

    grant = DatasetGrant(account_id=tech.id, dataset_id=dataset.id)
    db.add(grant)
    db.flush()

    # Tạo Source và Version
    src = Source(dataset_id=dataset.id, logical_filename="safety_sop.txt", profile_id="sop")
    db.add(src)
    db.flush()
    ver = SourceVersion(source_id=src.id, version_number=1, content_hash="hsec", storage_key="ksec", size_bytes=100, mime_type="text/plain")
    db.add(ver)
    db.flush()
    src.active_version_id = ver.id
    job = ImportJob(source_version_id=ver.id, state="ready")
    db.add(job)
    db.flush()
    run = ParseRun(source_version_id=ver.id, job_id=job.id, parser_name="text_log", parser_version="1.0", status="published")
    db.add(run)
    db.flush()
    rec = CanonicalRecord(
        parse_run_id=run.id, source_version_id=ver.id, dataset_id=dataset.id, position=1,
        locator_data={"line_start": 1, "line_end": 5},
        content_text="Quy định an toàn lao động tại trạm bốc dỡ hàng nguy hiểm.",
    )
    db.add(rec)
    db.commit()

    # 2. Tech đăng nhập
    login_res = client.post("/api/v1/auth/login", json={"username": "tech_recheck", "password": PASSWORD}, headers=HEADERS)
    h = {**HEADERS, "X-CSRF-Token": login_res.json()["csrf_token"]}

    # 3. Khi còn quyền: Tech gọi xem preview citation thành công (200 OK)
    prev_url = f"/api/v1/chat/citations/preview?dataset_id={dataset.id}&source_id={src.id}&citation_index=1"
    res_ok = client.get(prev_url, headers=h)
    assert res_ok.status_code == 200
    data_ok = res_ok.json()
    assert data_ok["logical_filename"] == "safety_sop.txt"
    assert "Quy định an toàn" in data_ok["excerpt_text"]

    # 4. Tạo 1 session có tin nhắn trích dẫn dataset này
    session = ChatSession(account_id=tech.id, title="Phiên thảo luận SOP an toàn")
    db.add(session)
    db.flush()
    msg = ChatMessage(
        session_id=session.id,
        role="assistant",
        content="Xem quy định an toàn [1]",
        citations=[{
            "citation_index": 1,
            "dataset_id": str(dataset.id),
            "source_id": str(src.id),
            "source_version": 1,
            "locator": {"source_id": str(src.id), "source_version": 1, "line_start": 1},
            "excerpt_text": rec.content_text,
        }],
    )
    db.add(msg)
    db.commit()

    # Kiểm tra trước khi thu hồi: lịch sử tin nhắn chứa citation
    res_msg_before = client.get(f"/api/v1/chat/sessions/{session.id}/messages", headers=h)
    assert res_msg_before.status_code == 200
    assert len(res_msg_before.json()[0]["citations"]) == 1

    # 5. Thu hồi quyền Dataset của Tech
    db.delete(grant)
    db.commit()

    # 6. Live Scope Recheck (D-05): Tech gọi lại preview citation -> BỊ CHẶN NGAY VỚI 403
    res_denied = client.get(prev_url, headers=h)
    assert res_denied.status_code == 403
    assert "thu hồi" in res_denied.json()["detail"]

    # 7. Kiểm tra lịch sử tin nhắn: citation của dataset bị thu hồi đã bị loại bỏ
    res_msg_after = client.get(f"/api/v1/chat/sessions/{session.id}/messages", headers=h)
    assert res_msg_after.status_code == 200
    assert len(res_msg_after.json()[0]["citations"]) == 0

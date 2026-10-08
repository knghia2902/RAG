from uuid import uuid4
import pytest
from app.auth.passwords import hash_password
from app.database.models import Account, Dataset, DatasetGrant, Source, SourceVersion, CanonicalRecord, ParseRun, ImportJob
from app.database.sources import index_source_version
from app.providers.fake import FakeEmbeddingAdapter
from tests.conftest import HEADERS, PASSWORD


def test_chat_session_lifecycle_and_isolation(client, db):
    # 1. Tạo 2 tài khoản: User 1 và User 2
    user1 = Account(username="user1_chat", display_name="User 1", role="technician", password_hash=hash_password(PASSWORD))
    user2 = Account(username="user2_chat", display_name="User 2", role="technician", password_hash=hash_password(PASSWORD))
    db.add_all([user1, user2])
    db.commit()

    # Login User 1
    login1 = client.post("/api/v1/auth/login", json={"username": "user1_chat", "password": PASSWORD}, headers=HEADERS)
    csrf1 = login1.json()["csrf_token"]
    h1 = {**HEADERS, "X-CSRF-Token": csrf1}

    # Login User 2
    login2 = client.post("/api/v1/auth/login", json={"username": "user2_chat", "password": PASSWORD}, headers=HEADERS)
    csrf2 = login2.json()["csrf_token"]
    h2 = {**HEADERS, "X-CSRF-Token": csrf2}

    # 2. User 1 tạo phiên chat mới
    res_create = client.post("/api/v1/chat/sessions", headers=h1)
    assert res_create.status_code == 201
    session_id = res_create.json()["id"]

    # 3. User 1 lấy danh sách phiên chat
    res_list = client.get("/api/v1/chat/sessions", headers=h1)
    assert res_list.status_code == 200
    assert any(s["id"] == session_id for s in res_list.json())

    # 4. T-03-11: User 2 cố tình truy cập phiên chat của User 1 -> 404
    res_cross = client.get(f"/api/v1/chat/sessions/{session_id}/messages", headers=h2)
    assert res_cross.status_code == 404

    # 5. User 1 xóa phiên chat
    res_del = client.delete(f"/api/v1/chat/sessions/{session_id}", headers=h1)
    assert res_del.status_code == 200

    # Sau khi xóa, User 1 không thể truy cập
    res_after = client.get(f"/api/v1/chat/sessions/{session_id}/messages", headers=h1)
    assert res_after.status_code == 404


def test_chat_query_execution_and_message_retrieval(client, db):
    # Tạo user và dataset có dữ liệu
    user = Account(username="tech_qa", display_name="Tech QA", role="technician", password_hash=hash_password(PASSWORD))
    dataset = Dataset(name=f"Dataset-QA-{uuid4().hex[:8]}")
    db.add_all([user, dataset])
    db.flush()

    grant = DatasetGrant(account_id=user.id, dataset_id=dataset.id)
    db.add(grant)
    db.flush()

    src = Source(dataset_id=dataset.id, logical_filename="sop_kho.txt", profile_id="sop")
    db.add(src)
    db.flush()
    ver = SourceVersion(source_id=src.id, version_number=1, content_hash="h1", storage_key="k1", size_bytes=100, mime_type="text/plain")
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
        locator_data={"page": 1, "line_start": 5, "line_end": 10},
        content_text="Quy trình kiểm tra mã đơn DH001: kiểm tra cảm biến quang tại trạm phân loại.",
    )
    db.add(rec)
    db.commit()

    # Index embeddings
    fake_provider = FakeEmbeddingAdapter()
    index_source_version(db, ver.id, provider=fake_provider)

    # Đăng nhập
    login_res = client.post("/api/v1/auth/login", json={"username": "tech_qa", "password": PASSWORD}, headers=HEADERS)
    h = {**HEADERS, "X-CSRF-Token": login_res.json()["csrf_token"]}

    # Gửi câu hỏi
    query_payload = {
        "question": "Quy trình kiểm tra đơn hàng DH001 thế nào?",
        "dataset_ids": [str(dataset.id)],
    }
    query_res = client.post("/api/v1/chat/query", json=query_payload, headers=h)
    assert query_res.status_code == 200
    data = query_res.json()

    assert "session_id" in data
    assert "message" in data
    assert data["message"]["role"] == "assistant"
    assert len(data["message"]["content"]) > 0

    # Lấy lại lịch sử tin nhắn
    session_id = data["session_id"]
    msg_res = client.get(f"/api/v1/chat/sessions/{session_id}/messages", headers=h)
    assert msg_res.status_code == 200
    messages = msg_res.json()
    assert len(messages) >= 2  # user và assistant
    assert messages[0]["role"] == "user"
    assert messages[1]["role"] == "assistant"

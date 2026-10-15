import os
from pathlib import Path
from uuid import uuid4
from PIL import Image
import pytest
from sqlalchemy import delete
from app.auth.passwords import hash_password
from app.database.models import (
    Account,
    Dataset,
    DatasetGrant,
    ExtractedImage,
    Source,
    SourceVersion,
)
from scripts.bootstrap_admin import bootstrap_admin
from tests.conftest import HEADERS, PASSWORD


@pytest.fixture
def sample_image_file(tmp_path: Path):
    """Tạo một file ảnh PNG mẫu thực tế để phục vụ kiểm thử."""
    img_dir = tmp_path / "images"
    img_dir.mkdir(parents=True, exist_ok=True)
    img_file = img_dir / f"test_{uuid4().hex[:8]}.png"
    img = Image.new("RGBA", (120, 80), color=(0, 128, 255, 255))
    img.save(img_file, format="PNG")
    return img_file


@pytest.fixture
def image_fixture(db, sample_image_file):
    """
    Thiết lập cấu trúc cơ sở dữ liệu:
    - Technician account
    - Dataset A (được cấp quyền) và Dataset B (không được cấp quyền)
    - Source và SourceVersion cho Dataset A và Dataset B
    - ExtractedImage cho Dataset A và Dataset B trỏ tới sample_image_file
    """
    tech = Account(
        username=f"tech_img_{uuid4().hex[:6]}",
        display_name="Tech Image ACL",
        role="technician",
        password_hash=hash_password(PASSWORD),
    )
    dataset_a = Dataset(name=f"Dataset-A-{uuid4().hex[:8]}")
    dataset_b = Dataset(name=f"Dataset-B-{uuid4().hex[:8]}")
    db.add_all([tech, dataset_a, dataset_b])
    db.flush()

    # Cấp quyền dataset_a cho tech
    grant_a = DatasetGrant(account_id=tech.id, dataset_id=dataset_a.id)
    db.add(grant_a)
    db.flush()

    # Source và SourceVersion cho dataset_a
    source_a = Source(dataset_id=dataset_a.id, logical_filename="sop_logistics.pdf", profile_id="pdf_docx")
    db.add(source_a)
    db.flush()

    version_a = SourceVersion(
        source_id=source_a.id,
        version_number=1,
        content_hash="hash_a",
        storage_key="key_a",
        size_bytes=1024,
        mime_type="application/pdf",
    )
    db.add(version_a)
    db.flush()
    source_a.active_version_id = version_a.id

    # ExtractedImage trong dataset_a
    image_a = ExtractedImage(
        id=uuid4(),
        dataset_id=dataset_a.id,
        source_version_id=version_a.id,
        page_number=1,
        image_type="embedded",
        storage_path=str(sample_image_file),
        mime_type="image/png",
        width=120,
        height=80,
        size_bytes=sample_image_file.stat().st_size,
        caption="Sơ đồ quy trình kho A",
    )
    db.add(image_a)

    # Source, Version và Image trong dataset_b (tech KHÔNG có quyền)
    source_b = Source(dataset_id=dataset_b.id, logical_filename="confidential.pdf", profile_id="pdf_docx")
    db.add(source_b)
    db.flush()

    version_b = SourceVersion(
        source_id=source_b.id,
        version_number=1,
        content_hash="hash_b",
        storage_key="key_b",
        size_bytes=2048,
        mime_type="application/pdf",
    )
    db.add(version_b)
    db.flush()
    source_b.active_version_id = version_b.id

    image_b = ExtractedImage(
        id=uuid4(),
        dataset_id=dataset_b.id,
        source_version_id=version_b.id,
        page_number=2,
        image_type="rendered_page",
        storage_path=str(sample_image_file),
        mime_type="image/png",
        width=120,
        height=80,
        size_bytes=sample_image_file.stat().st_size,
        caption="Tài liệu bảo mật B",
    )
    db.add(image_b)

    db.commit()

    return {
        "tech": tech,
        "dataset_a": dataset_a,
        "dataset_b": dataset_b,
        "source_a": source_a,
        "source_b": source_b,
        "version_a": version_a,
        "version_b": version_b,
        "image_a": image_a,
        "image_b": image_b,
        "sample_image_file": sample_image_file,
    }


def login_user(client, username, password=PASSWORD):
    res = client.post(
        "/api/v1/auth/login",
        json={"username": username, "password": password},
        headers=HEADERS,
    )
    assert res.status_code == 200, res.text
    csrf = res.json()["csrf_token"]
    return {**HEADERS, "X-CSRF-Token": csrf}


def test_get_image_success_for_authorized_technician(client, image_fixture):
    """Kỹ thuật viên có quyền trên dataset A tải thành công ảnh với đầy đủ metadata và header bảo mật."""
    data = image_fixture
    tech_headers = login_user(client, data["tech"].username)

    url = f"/api/v1/datasets/{data['dataset_a'].id}/sources/{data['source_a'].id}/images/{data['image_a'].id}"
    res = client.get(url, headers=tech_headers)

    assert res.status_code == 200
    assert res.headers["content-type"] == "image/png"
    assert "private" in res.headers["cache-control"]
    assert "max-age=3600" in res.headers["cache-control"]
    assert res.headers["x-content-type-options"] == "nosniff"
    assert res.content == data["sample_image_file"].read_bytes()


def test_get_image_forbidden_for_unauthorized_dataset(client, image_fixture):
    """Kỹ thuật viên không có quyền trên dataset B bị từ chối với 403 Forbidden."""
    data = image_fixture
    tech_headers = login_user(client, data["tech"].username)

    url = f"/api/v1/datasets/{data['dataset_b'].id}/sources/{data['source_b'].id}/images/{data['image_b'].id}"
    res = client.get(url, headers=tech_headers)

    assert res.status_code == 403
    assert "không có quyền" in res.json()["detail"].lower()


def test_live_scope_recheck_revocation(client, db, image_fixture):
    """
    Live Scope Recheck: Ban đầu kỹ thuật viên tải được ảnh (200 OK),
    khi bị thu hồi quyền trong DB, yêu cầu tải lại ngay lập tức bị từ chối 403 Forbidden (AUTH-04, T-07-03).
    """
    data = image_fixture
    tech_headers = login_user(client, data["tech"].username)

    url = f"/api/v1/datasets/{data['dataset_a'].id}/sources/{data['source_a'].id}/images/{data['image_a'].id}"
    
    # 1. Tải ảnh lần đầu thành công
    res_ok = client.get(url, headers=tech_headers)
    assert res_ok.status_code == 200

    # 2. Thu hồi quyền trong cơ sở dữ liệu (xóa DatasetGrant)
    db.execute(
        delete(DatasetGrant).where(
            DatasetGrant.account_id == data["tech"].id,
            DatasetGrant.dataset_id == data["dataset_a"].id,
        )
    )
    db.commit()

    # 3. Yêu cầu tải lại ảnh lập tức trả về 403 Forbidden
    res_revoked = client.get(url, headers=tech_headers)
    assert res_revoked.status_code == 403
    assert "không có quyền" in res_revoked.json()["detail"].lower()


def test_unauthenticated_request_rejected(client, image_fixture):
    """Yêu cầu tải ảnh không có session hoặc token xác thực bị từ chối 401 Unauthorized."""
    data = image_fixture
    client.cookies.clear()

    url = f"/api/v1/datasets/{data['dataset_a'].id}/sources/{data['source_a'].id}/images/{data['image_a'].id}"
    res = client.get(url, headers=HEADERS)

    assert res.status_code == 401


def test_get_image_cross_tenant_idor_rejected(client, image_fixture):
    """
    Chống IDOR / Cross-Tenant: Kỹ thuật viên dùng dataset_a (hợp lệ) để truy vấn image_b (thuộc dataset_b)
    phải nhận 404 Không tìm thấy, không bị rò rỉ dữ liệu giữa các dataset (T-07-02).
    """
    data = image_fixture
    tech_headers = login_user(client, data["tech"].username)

    url = f"/api/v1/datasets/{data['dataset_a'].id}/sources/{data['source_a'].id}/images/{data['image_b'].id}"
    res = client.get(url, headers=tech_headers)

    assert res.status_code == 404
    assert "không tìm thấy" in res.json()["detail"].lower()


def test_get_image_physical_file_missing_returns_404(client, image_fixture):
    """Khi tệp ảnh vật lý bị xóa hoặc thất lạc trên đĩa lưu trữ, API trả về 404 rõ ràng."""
    data = image_fixture
    tech_headers = login_user(client, data["tech"].username)

    # Xóa file vật lý
    os.remove(data["sample_image_file"])

    url = f"/api/v1/datasets/{data['dataset_a'].id}/sources/{data['source_a'].id}/images/{data['image_a'].id}"
    res = client.get(url, headers=tech_headers)

    assert res.status_code == 404
    assert "không tồn tại" in res.json()["detail"].lower()


def test_admin_can_access_any_dataset_image(client, image_fixture):
    """Admin có toàn quyền truy cập hình ảnh trên mọi dataset mà không cần grant cụ thể."""
    data = image_fixture
    bootstrap_admin("admin", PASSWORD)
    admin_headers = login_user(client, "admin")

    # Admin truy cập ảnh thuộc dataset B
    url_b = f"/api/v1/datasets/{data['dataset_b'].id}/sources/{data['source_b'].id}/images/{data['image_b'].id}"
    res_b = client.get(url_b, headers=admin_headers)

    assert res_b.status_code == 200
    assert res_b.content == data["sample_image_file"].read_bytes()

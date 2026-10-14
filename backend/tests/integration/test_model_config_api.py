from fastapi.testclient import TestClient
from app.main import app
from app.database.models import Account
from scripts.bootstrap_admin import bootstrap_admin
from tests.conftest import PASSWORD, HEADERS


def test_model_config_api_permissions_and_response(client, db):
    # Create admin
    bootstrap_admin("admin_cfg", PASSWORD)

    # Login admin
    login_res = client.post(
        "/api/v1/auth/login",
        json={"username": "admin_cfg", "password": PASSWORD},
        headers=HEADERS,
    )
    assert login_res.status_code == 200
    admin_csrf = login_res.json()["csrf_token"]

    # Create technician
    tech = Account(username="tech_cfg", display_name="Tech Config", password_hash="hash", role="technician")
    db.add(tech)
    db.commit()

    # Admin accesses GET /api/v1/config/models
    res = client.get(
        "/api/v1/config/models",
        headers={**HEADERS, "X-CSRF-Token": admin_csrf},
    )
    assert res.status_code == 200
    data = res.json()
    assert "embedding_model" in data
    assert data["embedding_dimension"] == 1536
    assert "llm_model" in data
    assert "openai_configured" in data
    # Ensure no raw API keys are exposed
    assert "sk-" not in str(data)

    # Admin updates model configuration
    post_res = client.post(
        "/api/v1/config/models",
        json={"llm_model": "gpt-4o"},
        headers={**HEADERS, "X-CSRF-Token": admin_csrf},
    )
    assert post_res.status_code == 200
    assert post_res.json()["llm_model"] == "gpt-4o"

    # Reset back to default
    client.post(
        "/api/v1/config/models",
        json={"llm_model": "gpt-4o-mini"},
        headers={**HEADERS, "X-CSRF-Token": admin_csrf},
    )

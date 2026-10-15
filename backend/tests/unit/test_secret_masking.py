from app.llm.secret_masking import mask_secrets


def test_mask_openai_api_key():
    raw = "Vui lòng gọi OpenAI với key sk-proj-1234567890abcdef1234567890 trong cấu hình."
    sanitized = mask_secrets(raw)
    assert "sk-[REDACTED]" in sanitized
    assert "1234567890abcdef" not in sanitized


def test_mask_bearer_token():
    raw = "Request header: Bearer abcdef1234567890abcdef1234567890 sent to upstream."
    sanitized = mask_secrets(raw)
    assert "Bearer [REDACTED]" in sanitized
    assert "abcdef1234567890" not in sanitized


def test_mask_password_and_secret_fields():
    raw1 = "Configured: password = 'mySuperSecretPassword123' for user admin."
    raw2 = "API call headers: api_key: 'top_secret_token_12345' sent."
    assert "password=[REDACTED]" in mask_secrets(raw1)
    assert "mySuperSecretPassword123" not in mask_secrets(raw1)
    assert "api_key=[REDACTED]" in mask_secrets(raw2)
    assert "top_secret_token_12345" not in mask_secrets(raw2)


def test_mask_database_uri_password():
    raw = "Connecting to postgresql://rag_user:super_secret_pw@postgres-test:5432/rag_test"
    sanitized = mask_secrets(raw)
    assert "postgresql://rag_user:[REDACTED]@postgres-test:5432/rag_test" in sanitized
    assert "super_secret_pw" not in sanitized


def test_mask_private_key_block():
    raw = (
        "Here is the key:\n"
        "-----BEGIN RSA PRIVATE KEY-----\n"
        "MIIEowIBAAKCAQEA0Y1234567890abcdefghijk\n"
        "-----END RSA PRIVATE KEY-----\n"
        "End of log."
    )
    sanitized = mask_secrets(raw)
    assert "[REDACTED_PRIVATE_KEY]" in sanitized
    assert "MIIEowIBAAKCAQEA" not in sanitized


def test_preserve_non_secret_identifiers():
    # Order IDs, error codes, UUIDs, and normal operational terms must NOT be masked
    text = "Đơn hàng DH001 và DH010 gặp lỗi ERR-502 tại WMS kho Sóng Thần, UUID c9bf9e57-1685-4c89-bafb-ff5af830be8a."
    sanitized = mask_secrets(text)
    assert sanitized == text
    assert "DH001" in sanitized
    assert "DH010" in sanitized
    assert "ERR-502" in sanitized
    assert "c9bf9e57-1685-4c89-bafb-ff5af830be8a" in sanitized


def test_mask_gemini_api_key():
    raw1 = "Configured Gemini key: AQ.Ab8RN6JPfDummyFakeKeyForTestingSecretMaskingOnly1234 in settings."
    sanitized1 = mask_secrets(raw1)
    assert "[REDACTED_GEMINI_KEY]" in sanitized1
    assert "Ab8RN6JPf" not in sanitized1

    raw2 = "Legacy Google key AIzaSyD-abc123DEF456ghi789JKL012mno3456 detected in logs."
    sanitized2 = mask_secrets(raw2)
    assert "[REDACTED_GEMINI_KEY]" in sanitized2
    assert "AIzaSyD" not in sanitized2

from functools import lru_cache
from urllib.parse import urlparse
from pydantic import SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=None, extra="ignore")
    database_url: SecretStr
    app_origin: str = "http://localhost:3000"
    test_mode: bool = False
    openai_api_key: SecretStr = SecretStr("")
    gemini_api_key: SecretStr = SecretStr("")
    llm_provider: str = "gemini"

    @model_validator(mode="after")
    def loopback_only(self):
        parsed = urlparse(self.app_origin)
        allowed = {"localhost", "127.0.0.1", "::1"}
        if self.test_mode:
            allowed.add("next-test")
        if parsed.scheme != "http" or parsed.hostname not in allowed or parsed.path or parsed.query or parsed.fragment:
            raise ValueError("APP_ORIGIN must be an exact HTTP loopback origin")
        if self.test_mode:
            db = urlparse(self.database_url.get_secret_value())
            if db.hostname != "postgres-test" or db.path != "/rag_test":
                raise ValueError("Test mode requires isolated postgres-test/rag_test")
        return self


@lru_cache
def get_settings():
    return Settings()

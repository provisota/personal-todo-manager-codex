from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    environment: str = "local"
    database_url: str = "postgresql+asyncpg://todo:todo@localhost:5432/todo"
    backend_base_url: str = "http://localhost:8000"
    frontend_base_url: str = "http://localhost:5173"
    session_secret: str = "local-dev-secret-change-me"
    cookie_secure: bool = False
    cookie_domain: str | None = None
    access_token_ttl_minutes: int = 60 * 24 * 7
    ws_notification_interval_seconds: int = 60
    cors_allowed_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    cors_allowed_origin_regex: str | None = r"^http://(localhost|127\.0\.0\.1):517[0-9]$"
    test_auth_enabled: bool = False

    google_client_id: str = ""
    google_client_secret: str = ""
    github_client_id: str = ""
    github_client_secret: str = ""

    @property
    def cors_origins(self) -> list[str]:
        return [item.strip() for item in self.cors_allowed_origins.split(",") if item.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()

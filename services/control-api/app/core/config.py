from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    service_name: str = "control-api"
    database_url: str = "postgresql+asyncpg://mimicron:mimicron_dev@localhost:5432/mimicron"
    redis_url: str = "redis://localhost:6379/0"
    jwt_secret: str = "dev-jwt-secret-change-me"
    internal_api_secret: str = "dev-internal-secret-change-me"
    jwt_access_ttl_seconds: int = 900
    jwt_refresh_ttl_seconds: int = 604800
    api_key_cache_ttl_seconds: int = 300
    log_level: str = "INFO"

    @property
    def database_url_sync(self) -> str:
        return self.database_url.replace("+asyncpg", "")


settings = Settings()

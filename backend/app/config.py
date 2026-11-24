"""Application configuration loaded from environment variables."""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Strongly-typed application settings.

    Values are read from environment variables or a ``.env`` file located in the
    backend working directory. See ``.env.example``.
    """

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    cricapi_base_url: str = "https://api.cricapi.com/v1"
    cricapi_api_key: str = ""
    database_url: str = "sqlite:///./cricstat.db"
    app_env: str = "development"
    log_level: str = "INFO"
    cache_ttl_seconds: int = 3600

    @property
    def has_api_key(self) -> bool:
        return bool(self.cricapi_api_key and self.cricapi_api_key != "your_api_key_here")


settings = Settings()
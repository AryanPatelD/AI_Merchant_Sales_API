"""Application configuration loaded from environment variables."""

from functools import lru_cache
from uuid import UUID

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Validated runtime settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "AI Merchant Sales API"
    api_v1_prefix: str = "/api/v1"
    database_url: str
    merchant_id: UUID = UUID("00000000-0000-0000-0000-000000000001")
    merchant_api_version: str = "1.0"
    quote_validity_seconds: int = Field(default=300, ge=60, le=3600)
    enabled_payment_gateways: list[str] = Field(default_factory=list)


@lru_cache
def get_settings() -> Settings:
    return Settings()

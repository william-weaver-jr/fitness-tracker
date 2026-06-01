"""Application configuration loaded from environment variables."""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Runtime
    env: str = Field(default="development", alias="ENV")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    # HTTP server
    host: str = Field(default="0.0.0.0", alias="HOST")
    port: int = Field(default=8000, alias="PORT")

    # Oracle
    oracle_host: str = Field(default="localhost", alias="ORACLE_HOST")
    oracle_port: int = Field(default=1521, alias="ORACLE_PORT")
    oracle_service_name: str = Field(default="FREEPDB1", alias="ORACLE_SERVICE_NAME")
    oracle_user: str = Field(default="fittrack_app", alias="ORACLE_USER")
    oracle_password: str = Field(default="", alias="ORACLE_PASSWORD")
    oracle_pool_min: int = Field(default=2, alias="ORACLE_POOL_MIN")
    oracle_pool_max: int = Field(default=10, alias="ORACLE_POOL_MAX")
    oracle_pool_increment: int = Field(default=1, alias="ORACLE_POOL_INCREMENT")

    # Redis
    redis_url: str = Field(default="redis://localhost:6379/0", alias="REDIS_URL")

    # CORS
    cors_allowed_origins: list[str] = Field(
        default=["http://localhost:5173", "http://localhost:8000"],
        alias="CORS_ALLOWED_ORIGINS",
    )

    # Dev test page
    enable_dev_test_page: bool = Field(default=True, alias="ENABLE_DEV_TEST_PAGE")

    @property
    def is_production(self) -> bool:
        return self.env.lower() == "production"

    @property
    def is_development(self) -> bool:
        return self.env.lower() == "development"

    @property
    def oracle_dsn(self) -> str:
        return f"{self.oracle_host}:{self.oracle_port}/{self.oracle_service_name}"


@lru_cache
def get_settings() -> Settings:
    return Settings()

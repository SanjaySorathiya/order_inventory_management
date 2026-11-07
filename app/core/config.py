"""Validated application settings loaded from environment variables."""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    """Process environment overrides the optional project-root .env file."""

    model_config = SettingsConfigDict(
        env_prefix="OIM_",
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
        str_strip_whitespace=True,
    )

    app_name: str = Field(default="Order & Inventory Management API", min_length=1)
    environment: Literal["development", "test", "production"] = "development"
    debug: bool = False


@lru_cache
def get_settings() -> Settings:
    """Load once per process; restart after editing environment settings."""
    return Settings()

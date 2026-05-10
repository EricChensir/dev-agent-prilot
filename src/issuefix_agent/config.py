from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration loaded from environment variables and .env."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    openai_api_key: str | None = Field(default=None, alias="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-5.2", alias="OPENAI_MODEL")
    max_context_chars: int = Field(default=45_000, alias="ISSUEFIX_MAX_CONTEXT_CHARS")
    max_file_chars: int = Field(default=12_000, alias="ISSUEFIX_MAX_FILE_CHARS")
    max_files: int = Field(default=24, alias="ISSUEFIX_MAX_FILES")


def get_settings() -> Settings:
    return Settings()

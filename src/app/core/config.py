from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Resume Vacancy AI Agent"
    environment: str = "local"
    debug: bool = False
    api_prefix: str = "/api/v1"
    database_url: str = "postgresql+psycopg://resume_agent:resume_agent@localhost:5432/resume_agent"
    qdrant_url: str = "http://localhost:6333"
    qdrant_collection: str = "resume_examples"
    llm_provider: str = "disabled"
    llm_base_url: str = "https://api.openai.com/v1"
    llm_api_key: str | None = None
    llm_model: str = "gpt-4o-mini"
    llm_timeout_seconds: float = Field(default=30.0, gt=0)
    log_level: str = Field(default="INFO", pattern="^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()

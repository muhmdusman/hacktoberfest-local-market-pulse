"""Application settings loaded from environment variables and the root .env.local file."""

from functools import lru_cache
from pathlib import Path

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

# backend/app/core/config.py -> parents[3] is the repository root
ROOT_DIR = Path(__file__).resolve().parents[3]
ENV_FILE = ROOT_DIR / ".env.local"


class Settings(BaseSettings):
    """Typed app configuration. Real environment variables override .env.local values."""

    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore",  # .env.local also holds Docker-only vars (POSTGRES_*)
    )

    app_name: str = "Hacktober API"
    app_env: str = "local"
    api_v1_prefix: str = "/api/v1"
    log_level: str = "INFO"

    database_url: str
    db_echo: bool = False

    # ---- LLM (open-weight, <= 8B, enforced by app.llm.registry) ----
    groq_api_key: SecretStr | None = None
    llm_model: str = "allam-2-7b"
    llm_temperature: float = 0.0
    llm_max_tokens: int = 512
    llm_timeout_s: float = 30.0
    llm_max_retries: int = 3  # client-side exponential backoff on 429 / 5xx
    llm_max_concurrency: int = 4


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance so .env.local is parsed only once."""
    return Settings()

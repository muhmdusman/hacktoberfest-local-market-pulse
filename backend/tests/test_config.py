"""Tests for app/core/config.py"""

import pytest
from pydantic import ValidationError

from app.core.config import ENV_FILE, Settings, get_settings


def test_env_file_resolves_to_repo_root_env_local():
    assert ENV_FILE.name == ".env.local"
    assert ENV_FILE.exists(), f"Expected {ENV_FILE} to exist"


def test_settings_load_async_database_url_from_env_file():
    settings = Settings()
    assert settings.database_url.startswith("postgresql+asyncpg://")


def test_settings_defaults():
    settings = Settings()
    assert settings.api_v1_prefix == "/api/v1"
    assert settings.db_echo is False


def test_environment_variable_overrides_env_file(monkeypatch):
    monkeypatch.setenv("APP_NAME", "Override API")
    assert Settings().app_name == "Override API"


def test_missing_database_url_raises_validation_error(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    with pytest.raises(ValidationError):
        Settings(_env_file=None)


def test_get_settings_is_cached():
    assert get_settings() is get_settings()

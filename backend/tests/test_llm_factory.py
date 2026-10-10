"""Tests for app/llm/factory.py"""

import pytest

from app.core.config import get_settings
from app.llm.factory import LLMNotConfiguredError, ensure_llm_ready, get_chat_model
from app.llm.registry import ModelNotAllowedError


def test_get_chat_model_uses_configured_eligible_model():
    llm = get_chat_model()
    assert llm.model_name == get_settings().llm_model
    assert llm.max_retries == get_settings().llm_max_retries


def test_missing_api_key_raises(monkeypatch):
    monkeypatch.setattr(get_settings(), "groq_api_key", None)
    with pytest.raises(LLMNotConfiguredError):
        ensure_llm_ready()


def test_oversized_model_is_refused_before_any_call(monkeypatch):
    monkeypatch.setattr(get_settings(), "llm_model", "openai/gpt-oss-20b")
    with pytest.raises(ModelNotAllowedError):
        get_chat_model()

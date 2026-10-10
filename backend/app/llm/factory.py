"""Builds the LangChain chat model for the configured (registry-approved) model."""

from langchain_groq import ChatGroq

from app.core.config import get_settings
from app.llm.registry import ModelSpec, resolve_model


class LLMNotConfiguredError(RuntimeError):
    """Raised when no API key is available for the hosted model."""


def ensure_llm_ready() -> ModelSpec:
    """Check the 8B gate and the API key without making a network call."""
    settings = get_settings()
    spec = resolve_model(settings.llm_model)
    if settings.groq_api_key is None:
        raise LLMNotConfiguredError("GROQ_API_KEY is missing from .env.local")
    return spec


def get_chat_model() -> ChatGroq:
    settings = get_settings()
    spec = ensure_llm_ready()
    return ChatGroq(
        model=spec.id,
        api_key=settings.groq_api_key,
        temperature=settings.llm_temperature,
        max_tokens=settings.llm_max_tokens,
        timeout=settings.llm_timeout_s,
        max_retries=settings.llm_max_retries,
    )

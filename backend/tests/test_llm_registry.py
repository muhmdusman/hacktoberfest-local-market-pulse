"""Tests for app/llm/registry.py (the 8B gate)."""

import pytest

from app.llm.registry import MAX_PARAMS_B, REGISTRY, ModelNotAllowedError, ModelSpec, resolve_model


@pytest.mark.parametrize("model_id", ["allam-2-7b", "llama-3.1-8b-instant", "qwen3:4b"])
def test_eligible_models_resolve(model_id):
    spec = resolve_model(model_id)
    assert spec.params_b <= MAX_PARAMS_B
    assert spec.eligible


@pytest.mark.parametrize(
    "model_id", ["openai/gpt-oss-20b", "qwen/qwen3.8-27b", "llama-3.3-70b-versatile", "openai/gpt-oss-120b"]
)
def test_models_above_8b_are_rejected(model_id):
    with pytest.raises(ModelNotAllowedError, match="cap is 8B"):
        resolve_model(model_id)


def test_unknown_model_is_rejected():
    with pytest.raises(ModelNotAllowedError, match="Unknown model"):
        resolve_model("mystery-model")


def test_closed_model_is_rejected(monkeypatch):
    monkeypatch.setitem(REGISTRY, "closed-3b", ModelSpec("closed-3b", "x", 3.0, "Proprietary", open_weight=False))
    with pytest.raises(ModelNotAllowedError, match="not open-weight"):
        resolve_model("closed-3b")

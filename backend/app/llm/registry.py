"""Open-weight model registry. Enforces the hackathon's 8B parameter cap in code.

Rule: reject anything that is not open-weight or whose total parameter count
exceeds 8.5B (accepts the 8B class, e.g. Llama 3.1 8B = 8.03B; rejects 9B+).
MoE models count TOTAL parameters, not active ones (gpt-oss-20b is 21B total).
"""

from dataclasses import dataclass

MAX_PARAMS_B = 8.5


class ModelNotAllowedError(ValueError):
    """Raised when a configured model is unknown, closed, or above the cap."""


@dataclass(frozen=True)
class ModelSpec:
    id: str
    provider: str
    params_b: float
    license: str
    open_weight: bool = True

    @property
    def eligible(self) -> bool:
        return self.open_weight and self.params_b <= MAX_PARAMS_B


REGISTRY: dict[str, ModelSpec] = {
    spec.id: spec
    for spec in (
        # Eligible
        ModelSpec("allam-2-7b", "groq", 7.0, "Apache-2.0"),
        ModelSpec("llama-3.1-8b-instant", "groq", 8.03, "Llama 3.1 Community License"),
        ModelSpec("qwen3:4b", "ollama", 4.02, "Apache-2.0"),
        ModelSpec("qwen3:1.7b", "ollama", 2.03, "Apache-2.0"),
        # Listed so the gate can visibly reject them
        ModelSpec("openai/gpt-oss-20b", "groq", 20.9, "Apache-2.0"),
        ModelSpec("qwen/qwen3.8-27b", "groq", 27.0, "Apache-2.0"),
        ModelSpec("openai/gpt-oss-120b", "groq", 116.8, "Apache-2.0"),
        ModelSpec("llama-3.3-70b-versatile", "groq", 70.6, "Llama 3.3 Community License"),
    )
}


def resolve_model(model_id: str) -> ModelSpec:
    """Return the spec for an eligible model or raise ModelNotAllowedError."""
    spec = REGISTRY.get(model_id)
    if spec is None:
        raise ModelNotAllowedError(
            f"Unknown model '{model_id}'. Add it to app/llm/registry.py with its exact parameter count."
        )
    if not spec.open_weight:
        raise ModelNotAllowedError(f"'{model_id}' is not open-weight.")
    if spec.params_b > MAX_PARAMS_B:
        raise ModelNotAllowedError(
            f"'{model_id}' has {spec.params_b}B parameters; the event cap is 8B."
        )
    return spec

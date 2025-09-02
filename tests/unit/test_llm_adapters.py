from typing import Any

import pytest

from autoresearch.errors import LLMError
from autoresearch.llm.adapters import DummyAdapter, LLMAdapter


class EmptyAdapter(LLMAdapter):
    """Adapter with no declared models for testing defaults."""

    available_models: list[str] = []

    def generate(self, prompt: str, model: str | None = None, **kwargs: Any) -> str:
        return ""


@pytest.mark.requires_llm
def test_validate_model_defaults_to_available_first_model() -> None:
    adapter = DummyAdapter()
    assert adapter.validate_model(None) == "dummy-model"


@pytest.mark.requires_llm
def test_validate_model_uses_generic_default_when_no_models() -> None:
    adapter = EmptyAdapter()
    assert adapter.validate_model(None) == "default"


@pytest.mark.requires_llm
def test_validate_model_rejects_invalid_models() -> None:
    adapter = DummyAdapter()
    with pytest.raises(LLMError):
        adapter.validate_model("unknown")

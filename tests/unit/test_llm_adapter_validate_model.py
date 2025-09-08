import pytest

from autoresearch.errors import LLMError
from autoresearch.llm.adapters import DummyAdapter


@pytest.mark.requires_llm
def test_validate_model_invalid():
    """Invalid model names should raise LLMError."""
    adapter = DummyAdapter()
    with pytest.raises(LLMError):
        adapter.validate_model("invalid-model")

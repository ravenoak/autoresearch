import pytest

from autoresearch.errors import LLMError
from autoresearch.llm.adapters import DummyAdapter


def test_validate_model_defaults_to_available():
    adapter = DummyAdapter()
    assert adapter.validate_model(None) == "dummy-model"


def test_validate_model_rejects_unknown_model():
    adapter = DummyAdapter()
    with pytest.raises(LLMError):
        adapter.validate_model("other-model")

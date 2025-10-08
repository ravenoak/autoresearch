# mypy: ignore-errors
"""Tests for the API LLM utilities."""

from autoresearch.api.llm import get_available_adapters


def test_get_available_adapters():
    """Test that get_available_adapters returns an empty dict."""
    adapters = get_available_adapters()
    assert isinstance(adapters, dict)
    assert len(adapters) == 0

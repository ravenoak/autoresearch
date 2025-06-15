"""Tests for search backend integration.

This module contains tests for the integration between different search backends
and the main search functionality.
"""

import pytest
from autoresearch.search import Search
from autoresearch import cache
from autoresearch.config import ConfigModel


@pytest.fixture(autouse=True)
def cleanup_search():
    """Clean up the search system after each test.

    This fixture ensures that the search system is properly cleaned up
    after each test, preventing test pollution and resource leaks.
    """
    # Setup
    original_backends = Search.backends.copy()
    cache.clear()

    yield

    # Teardown
    Search.backends = original_backends
    cache.clear()


def test_multiple_backends_called_and_merged(monkeypatch):
    """Test that multiple search backends are called and results are merged.

    This test verifies that when multiple search backends are configured,
    all of them are called and their results are merged in the final output.
    """
    # Setup
    calls = []

    def backend1(query, max_results=5):
        calls.append("b1")
        return [{"title": "t1", "url": "u1"}]

    def backend2(query, max_results=5):
        calls.append("b2")
        return [{"title": "t2", "url": "u2"}]

    monkeypatch.setitem(Search.backends, "b1", backend1)
    monkeypatch.setitem(Search.backends, "b2", backend2)

    cfg = ConfigModel(loops=1, search_backends=["b1", "b2"])
    monkeypatch.setattr("autoresearch.search.get_config", lambda: cfg)

    # Execute
    results = Search.external_lookup("q", max_results=1)

    # Verify
    assert calls == ["b1", "b2"]
    assert results == [
        {"title": "t1", "url": "u1"},
        {"title": "t2", "url": "u2"},
    ]

import pytest

from autoresearch.search import Search
from autoresearch.config import ConfigModel


def test_multiple_backends_called_and_merged(monkeypatch):
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

    results = Search.external_lookup("q", max_results=1)
    assert calls == ["b1", "b2"]
    assert results == [
        {"title": "t1", "url": "u1"},
        {"title": "t2", "url": "u2"},
    ]

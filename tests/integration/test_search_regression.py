"""Regression test for search results stability."""

from autoresearch.search import Search
from autoresearch.config.models import ConfigModel


def test_search_results_stable(monkeypatch, search_baseline):
    """Search results remain stable across releases."""

    def backend(query, max_results=5):
        return [{"title": "example", "url": "https://example.com"}]

    monkeypatch.setitem(Search.backends, "dummy", backend)
    cfg = ConfigModel(loops=1)
    cfg.search.backends = ["dummy"]
    cfg.search.context_aware.enabled = False
    monkeypatch.setattr("autoresearch.search.core.get_config", lambda: cfg)

    results = Search.external_lookup("example")
    search_baseline(results)

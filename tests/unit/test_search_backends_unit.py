from autoresearch.search import Search
from autoresearch.config import ConfigModel


def test_register_backend_and_lookup(monkeypatch):
    Search.backends = {}

    @Search.register_backend("dummy")
    def dummy_backend(query: str, max_results: int = 5):
        return [{"title": "t", "url": "u"}]

    cfg = ConfigModel(loops=1)
    cfg.search.backends = ["dummy"]
    cfg.search.context_aware.enabled = False
    monkeypatch.setattr("autoresearch.search.get_config", lambda: cfg)

    results = Search.external_lookup("x", max_results=1)
    assert results == [{"title": "t", "url": "u", "backend": "dummy"}]


def test_external_lookup_unknown_backend(monkeypatch):
    Search.backends = {}
    cfg = ConfigModel(loops=1)
    cfg.search.backends = ["unknown"]
    cfg.search.context_aware.enabled = False
    monkeypatch.setattr("autoresearch.search.get_config", lambda: cfg)

    results = Search.external_lookup("q", max_results=1)
    assert results and all("title" in r for r in results)

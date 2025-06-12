from autoresearch import cache
from autoresearch.search import Search
from autoresearch.config import ConfigModel


def test_search_uses_cache(monkeypatch):
    cache.clear()

    calls = {"count": 0}

    def backend(query: str, max_results: int = 5):
        calls["count"] += 1
        return [{"title": "Python", "url": "https://python.org"}]

    old_backends = Search.backends.copy()
    Search.backends = {"dummy": backend}
    cfg = ConfigModel(search_backends=["dummy"], loops=1)
    monkeypatch.setattr("autoresearch.search.get_config", lambda: cfg)

    # first call uses backend
    results1 = Search.external_lookup("python")
    assert calls["count"] == 1
    assert results1 == [{"title": "Python", "url": "https://python.org"}]

    # second call should be served from cache
    results2 = Search.external_lookup("python")
    assert calls["count"] == 1
    assert results2 == results1

    Search.backends = old_backends

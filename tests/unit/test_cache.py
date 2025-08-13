from threading import Thread

from autoresearch import cache
from autoresearch.search import Search
from autoresearch.config.models import ConfigModel


def test_search_uses_cache(monkeypatch):
    cache.clear()

    calls = {"count": 0}

    def backend(query: str, max_results: int = 5):
        calls["count"] += 1
        return [{"title": "Python", "url": "https://python.org"}]

    old_backends = Search.backends.copy()
    print(f"Original backends: {old_backends}")
    Search.backends = {"dummy": backend}
    print(f"New backends: {Search.backends}")
    cfg = ConfigModel.model_construct(loops=1)
    cfg.search.backends = ["dummy"]
    print(f"Config search backends: {cfg.search.backends}")
    # Disable context-aware search to avoid issues with SearchContext
    cfg.search.context_aware.enabled = False
    cfg.search.use_semantic_similarity = False
    monkeypatch.setattr("autoresearch.search.core.get_config", lambda: cfg)

    # first call uses backend
    results1 = Search.external_lookup("python")
    assert calls["count"] == 1
    # Check that the results contain the expected title and URL
    assert len(results1) == 1
    assert results1[0]["title"] == "Python"
    assert results1[0]["url"] == "https://python.org"

    # second call should be served from cache
    results2 = Search.external_lookup("python")
    assert calls["count"] == 1
    assert len(results2) == len(results1)
    assert results2[0]["title"] == results1[0]["title"]
    assert results2[0]["url"] == results1[0]["url"]

    Search.backends = old_backends


def test_cache_lifecycle(tmp_path):
    """Exercise basic cache operations using a temporary database."""
    orig_path = cache._db_path
    cache.teardown(remove_file=False)

    db_path = tmp_path / "cache.json"
    db1 = cache.setup(str(db_path))
    assert db_path.exists()

    # setup called again should return the same instance
    db2 = cache.setup(str(db_path))
    assert db1 is db2

    sample = [{"title": "t", "url": "u"}]
    cache.cache_results("q", "b", sample)
    assert cache.get_cached_results("q", "b") == sample

    cache.clear()
    assert cache.get_cached_results("q", "b") is None

    cache.teardown(remove_file=True)
    assert not db_path.exists()

    cache._db_path = orig_path


def test_setup_thread_safe(tmp_path):
    """Ensure multiple setup calls from threads share the same database."""
    orig_path = cache._db_path
    cache.teardown(remove_file=False)

    db_path = tmp_path / "cache.json"
    results = []

    def worker() -> None:
        results.append(cache.setup(str(db_path)))

    threads = [Thread(target=worker) for _ in range(5)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    first = results[0]
    assert all(db is first for db in results)

    cache.teardown(remove_file=True)
    cache._db_path = orig_path


def test_cache_is_backend_specific(monkeypatch):
    cache.clear()

    calls = {"b1": 0, "b2": 0}

    def backend1(query: str, max_results: int = 5):
        calls["b1"] += 1
        return [{"title": "B1", "url": "u1"}]

    def backend2(query: str, max_results: int = 5):
        calls["b2"] += 1
        return [{"title": "B2", "url": "u2"}]

    old_backends = Search.backends.copy()
    Search.backends = {"b1": backend1, "b2": backend2}

    cfg1 = ConfigModel.model_construct(loops=1)
    cfg1.search.backends = ["b1"]
    cfg1.search.context_aware.enabled = False
    cfg2 = ConfigModel.model_construct(loops=1)
    cfg2.search.backends = ["b2"]
    cfg2.search.context_aware.enabled = False

    monkeypatch.setattr("autoresearch.search.core.get_config", lambda: cfg1)
    results1 = Search.external_lookup("python")
    assert calls == {"b1": 1, "b2": 0}
    # Check that the results contain the expected title and URL
    assert len(results1) == 1
    assert results1[0]["title"] == "B1"
    assert results1[0]["url"] == "u1"

    monkeypatch.setattr("autoresearch.search.core.get_config", lambda: cfg2)
    results2 = Search.external_lookup("python")
    assert calls == {"b1": 1, "b2": 1}
    # Check that the results contain the expected title and URL
    assert len(results2) == 1
    assert results2[0]["title"] == "B2"
    assert results2[0]["url"] == "u2"

    monkeypatch.setattr("autoresearch.search.core.get_config", lambda: cfg1)
    results3 = Search.external_lookup("python")
    assert calls == {"b1": 1, "b2": 1}
    # Results should be the same as the first call (from cache)
    assert len(results3) == len(results1)
    assert results3[0]["title"] == results1[0]["title"]
    assert results3[0]["url"] == results1[0]["url"]

    Search.backends = old_backends

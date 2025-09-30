import importlib.util
from threading import Thread  # for thread-safety test
from typing import Any, Dict, List

import pytest
from pathlib import Path

if not importlib.util.find_spec("tinydb"):
    import tests.stubs.tinydb  # noqa: F401

from autoresearch.cache import SearchCache
from autoresearch.config.models import ConfigModel
from autoresearch.search import Search


def assert_bm25_signature(query: str, documents: List[Dict[str, Any]]) -> List[float]:
    """Ensure BM25 stub receives ``(query, documents)`` in that order."""
    assert isinstance(query, str)
    assert isinstance(documents, list)
    return [1.0] * len(documents)


@pytest.fixture(autouse=True)
def _skip_ontology_reasoner(monkeypatch) -> None:
    """Bypass heavy ontology reasoning in tests."""
    monkeypatch.setattr(
        "autoresearch.storage.run_ontology_reasoner",
        lambda *_, **__: None,
    )


def test_search_uses_cache(monkeypatch: pytest.MonkeyPatch) -> None:
    cache = SearchCache()
    search = Search(cache=cache)

    monkeypatch.setattr(
        Search,
        "calculate_bm25_scores",
        staticmethod(assert_bm25_signature),
    )

    calls = {"count": 0}

    def backend(query: str, max_results: int = 5):
        calls["count"] += 1
        return [{"title": "Python", "url": "https://python.org"}]

    with search.temporary_state() as s:
        s.backends = {"dummy": backend}
        cfg = ConfigModel.model_construct(loops=1)
        cfg.search.backends = ["dummy"]
        # Disable context-aware search to avoid issues with SearchContext
        cfg.search.context_aware.enabled = False
        cfg.search.use_semantic_similarity = False
        monkeypatch.setattr("autoresearch.search.core.get_config", lambda: cfg)

        # first call uses backend
        results1 = s.external_lookup("python")
        assert calls["count"] == 1
        assert len(results1) == 1
        assert results1[0]["title"] == "Python"
        assert results1[0]["url"] == "https://python.org"

        # second call should be served from cache
        results2 = s.external_lookup("python")
        assert calls["count"] == 1
        assert len(results2) == len(results1)
        assert results2[0]["title"] == results1[0]["title"]
        assert results2[0]["url"] == results1[0]["url"]


def test_cache_lifecycle(tmp_path: Path) -> None:
    """Exercise basic cache operations using a temporary database."""
    db_path = tmp_path / "cache.json"
    cache = SearchCache(str(db_path))

    assert db_path.exists()

    # setup called again should return the same instance
    db1 = cache.get_db()
    db2 = cache.setup(str(db_path))
    assert db1 is db2

    sample = [{"title": "t", "url": "u"}]
    cache.cache_results("q", "b", sample)
    assert cache.get_cached_results("q", "b") == sample

    cache.clear()
    assert cache.get_cached_results("q", "b") is None

    cache.teardown(remove_file=True)
    assert not db_path.exists()


def test_setup_thread_safe(tmp_path: Path) -> None:
    """Ensure multiple setup calls from threads share the same database."""
    cache = SearchCache(str(tmp_path / "cache.json"))
    results = []

    def worker() -> None:
        results.append(cache.setup())

    threads = [Thread(target=worker) for _ in range(5)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    first = results[0]
    assert all(db is first for db in results)

    cache.teardown(remove_file=True)


def test_cache_is_backend_specific(monkeypatch: pytest.MonkeyPatch) -> None:
    cache = SearchCache()
    search = Search(cache=cache)

    monkeypatch.setattr(
        Search,
        "calculate_bm25_scores",
        staticmethod(assert_bm25_signature),
    )

    calls = {"b1": 0, "b2": 0}

    def backend1(query: str, max_results: int = 5):
        calls["b1"] += 1
        return [{"title": "B1", "url": "u1"}]

    def backend2(query: str, max_results: int = 5):
        calls["b2"] += 1
        return [{"title": "B2", "url": "u2"}]

    with search.temporary_state() as s:
        s.backends = {"b1": backend1, "b2": backend2}

        cfg1 = ConfigModel.model_construct(loops=1)
        cfg1.search.backends = ["b1"]
        cfg1.search.context_aware.enabled = False
        cfg1.search.use_semantic_similarity = False
        cfg2 = ConfigModel.model_construct(loops=1)
        cfg2.search.backends = ["b2"]
        cfg2.search.context_aware.enabled = False
        cfg2.search.use_semantic_similarity = False

        monkeypatch.setattr("autoresearch.search.core.get_config", lambda: cfg1)
        results1 = s.external_lookup("python")
        assert calls == {"b1": 1, "b2": 0}
        assert len(results1) == 1
        assert results1[0]["title"] == "B1"
        assert results1[0]["url"] == "u1"
        # second call with backend1 should use cache
        results1_cached = s.external_lookup("python")
        assert calls == {"b1": 1, "b2": 0}
        assert len(results1_cached) == len(results1)
        assert results1_cached[0]["title"] == results1[0]["title"]
        assert results1_cached[0]["url"] == results1[0]["url"]

        monkeypatch.setattr("autoresearch.search.core.get_config", lambda: cfg2)
        results2 = s.external_lookup("python")
        assert calls == {"b1": 1, "b2": 1}
        assert len(results2) == 1
        assert results2[0]["title"] == "B2"
        assert results2[0]["url"] == "u2"
        # second call with backend2 should also use cache
        results2_cached = s.external_lookup("python")
        assert calls == {"b1": 1, "b2": 1}
        assert len(results2_cached) == len(results2)
        assert results2_cached[0]["title"] == results2[0]["title"]
        assert results2_cached[0]["url"] == results2[0]["url"]

        # switching back to backend1 should still use cached results
        monkeypatch.setattr("autoresearch.search.core.get_config", lambda: cfg1)
        results3 = s.external_lookup("python")
        assert calls == {"b1": 1, "b2": 1}
        assert len(results3) == len(results1)
        assert results3[0]["title"] == results1[0]["title"]
        assert results3[0]["url"] == results1[0]["url"]


def test_cache_is_backend_specific_without_embeddings(monkeypatch: pytest.MonkeyPatch) -> None:
    """Ensure cache separation without relying on embeddings."""
    cache = SearchCache()
    search = Search(cache=cache)

    monkeypatch.setattr(
        Search,
        "calculate_bm25_scores",
        staticmethod(assert_bm25_signature),
    )
    monkeypatch.setattr(
        Search,
        "get_sentence_transformer",
        staticmethod(lambda: None),
    )

    calls = {"b1": 0, "b2": 0}

    def backend1(query: str, max_results: int = 5):
        calls["b1"] += 1
        return [{"title": "B1", "url": "u1"}]

    def backend2(query: str, max_results: int = 5):
        calls["b2"] += 1
        return [{"title": "B2", "url": "u2"}]

    with search.temporary_state() as s:
        s.backends = {"b1": backend1, "b2": backend2}

        cfg1 = ConfigModel.model_construct(loops=1)
        cfg1.search.backends = ["b1"]
        cfg1.search.context_aware.enabled = False

        cfg2 = ConfigModel.model_construct(loops=1)
        cfg2.search.backends = ["b2"]
        cfg2.search.context_aware.enabled = False

        monkeypatch.setattr("autoresearch.search.core.get_config", lambda: cfg1)
        results1 = s.external_lookup("python")
        assert calls == {"b1": 1, "b2": 0}
        assert s.external_lookup("python") == results1
        assert calls == {"b1": 1, "b2": 0}

        monkeypatch.setattr("autoresearch.search.core.get_config", lambda: cfg2)
        results2 = s.external_lookup("python")
        assert calls == {"b1": 1, "b2": 1}
        assert s.external_lookup("python") == results2
        assert calls == {"b1": 1, "b2": 1}

        monkeypatch.setattr("autoresearch.search.core.get_config", lambda: cfg1)
        assert s.external_lookup("python") == results1
        assert calls == {"b1": 1, "b2": 1}


def test_context_aware_query_expansion_uses_cache(monkeypatch: pytest.MonkeyPatch) -> None:
    cache = SearchCache()
    search = Search(cache=cache)

    monkeypatch.setattr(
        Search,
        "calculate_bm25_scores",
        staticmethod(assert_bm25_signature),
    )

    calls = {"count": 0}

    def backend(query: str, max_results: int = 5):
        calls["count"] += 1
        return [{"title": "Python", "url": "https://python.org"}]

    class DummyContext:
        def expand_query(self, q: str) -> str:
            return q + " expanded"

        def add_to_history(self, q, results) -> None:  # pragma: no cover - no-op
            pass

        def build_topic_model(self) -> None:  # pragma: no cover - no-op
            pass

    with search.temporary_state() as s:
        s.backends = {"dummy": backend}
        cfg = ConfigModel.model_construct(loops=1)
        cfg.search.backends = ["dummy"]
        cfg.search.context_aware.enabled = True
        cfg.search.context_aware.use_topic_modeling = False
        cfg.search.use_semantic_similarity = False
        monkeypatch.setattr("autoresearch.search.core.get_config", lambda: cfg)
        monkeypatch.setattr(
            "autoresearch.search.core.SearchContext.get_instance",
            lambda: DummyContext(),
        )

        results1 = s.external_lookup("python")
        assert calls["count"] == 1
        results2 = s.external_lookup("python")
        assert calls["count"] == 1
        assert results2[0]["title"] == results1[0]["title"]
        assert results2[0]["url"] == results1[0]["url"]

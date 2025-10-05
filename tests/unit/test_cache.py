from __future__ import annotations

import importlib.util
from pathlib import Path
from threading import Thread  # for thread-safety test
from typing import Any, Dict, List, Tuple

import pytest

if not importlib.util.find_spec("tinydb"):
    import tests.stubs.tinydb  # noqa: F401

import numpy as np
from hypothesis import HealthCheck, given, settings, strategies as st

from autoresearch.cache import SearchCache
from autoresearch.config.models import ConfigModel
from autoresearch.search import Search


def assert_bm25_signature(query: str, documents: List[Dict[str, Any]]) -> List[float]:
    """Ensure BM25 stub receives ``(query, documents)`` in that order."""
    assert isinstance(query, str)
    assert isinstance(documents, list)
    return [1.0] * len(documents)


@pytest.fixture(autouse=True)
def _skip_ontology_reasoner(monkeypatch: pytest.MonkeyPatch) -> None:
    """Bypass heavy ontology reasoning in tests."""

    def _disable_reasoner(*_: Any, **__: Any) -> None:
        return None

    monkeypatch.setattr(
        "autoresearch.storage.run_ontology_reasoner",
        _disable_reasoner,
    )


def test_search_uses_cache(monkeypatch: pytest.MonkeyPatch) -> None:
    cache = SearchCache()
    search = Search(cache=cache)

    monkeypatch.setattr(
        Search,
        "calculate_bm25_scores",
        staticmethod(assert_bm25_signature),
    )

    calls: Dict[str, int] = {"count": 0}

    def backend(query: str, max_results: int = 5) -> List[Dict[str, str]]:
        calls["count"] += 1
        return [{"title": "Python", "url": "https://python.org"}]

    with search.temporary_state() as s:
        s.backends = {"dummy": backend}
        cfg = ConfigModel.model_construct(loops=1)
        cfg.search.backends = ["dummy"]
        # Disable context-aware search to avoid issues with SearchContext
        cfg.search.context_aware.enabled = False
        cfg.search.use_semantic_similarity = False
        cfg.search.query_rewrite.enabled = False
        cfg.search.adaptive_k.enabled = False

        def _get_config() -> ConfigModel:
            return cfg

        monkeypatch.setattr("autoresearch.search.core.get_config", _get_config)

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
    results: List[Any] = []

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

    calls: Dict[str, int] = {"b1": 0, "b2": 0}

    def backend1(query: str, max_results: int = 5) -> List[Dict[str, str]]:
        calls["b1"] += 1
        return [{"title": "B1", "url": "u1"}]

    def backend2(query: str, max_results: int = 5) -> List[Dict[str, str]]:
        calls["b2"] += 1
        return [{"title": "B2", "url": "u2"}]

    with search.temporary_state() as s:
        s.backends = {"b1": backend1, "b2": backend2}

        cfg1 = ConfigModel.model_construct(loops=1)
        cfg1.search.backends = ["b1"]
        cfg1.search.context_aware.enabled = False
        cfg1.search.use_semantic_similarity = False
        cfg1.search.query_rewrite.enabled = False
        cfg1.search.adaptive_k.enabled = False
        cfg2 = ConfigModel.model_construct(loops=1)
        cfg2.search.backends = ["b2"]
        cfg2.search.context_aware.enabled = False
        cfg2.search.use_semantic_similarity = False
        cfg2.search.query_rewrite.enabled = False
        cfg2.search.adaptive_k.enabled = False

        def _get_cfg1() -> ConfigModel:
            return cfg1

        def _get_cfg2() -> ConfigModel:
            return cfg2

        monkeypatch.setattr("autoresearch.search.core.get_config", _get_cfg1)
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

        monkeypatch.setattr("autoresearch.search.core.get_config", _get_cfg2)
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
        monkeypatch.setattr("autoresearch.search.core.get_config", _get_cfg1)
        results3 = s.external_lookup("python")
        assert calls == {"b1": 1, "b2": 1}
        assert len(results3) == len(results1)
        assert results3[0]["title"] == results1[0]["title"]
        assert results3[0]["url"] == results1[0]["url"]


def test_cache_is_backend_specific_without_embeddings(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Ensure cache separation without relying on embeddings."""
    cache = SearchCache()
    search = Search(cache=cache)

    monkeypatch.setattr(
        Search,
        "calculate_bm25_scores",
        staticmethod(assert_bm25_signature),
    )

    def _no_transformer() -> None:
        return None

    monkeypatch.setattr(
        Search,
        "get_sentence_transformer",
        staticmethod(_no_transformer),
    )

    calls: Dict[str, int] = {"b1": 0, "b2": 0}

    def backend1(query: str, max_results: int = 5) -> List[Dict[str, str]]:
        calls["b1"] += 1
        return [{"title": "B1", "url": "u1"}]

    def backend2(query: str, max_results: int = 5) -> List[Dict[str, str]]:
        calls["b2"] += 1
        return [{"title": "B2", "url": "u2"}]

    with search.temporary_state() as s:
        s.backends = {"b1": backend1, "b2": backend2}

        cfg1 = ConfigModel.model_construct(loops=1)
        cfg1.search.backends = ["b1"]
        cfg1.search.context_aware.enabled = False
        cfg1.search.use_semantic_similarity = False
        cfg1.search.query_rewrite.enabled = False
        cfg1.search.adaptive_k.enabled = False

        cfg2 = ConfigModel.model_construct(loops=1)
        cfg2.search.backends = ["b2"]
        cfg2.search.context_aware.enabled = False
        cfg2.search.use_semantic_similarity = False
        cfg2.search.query_rewrite.enabled = False
        cfg2.search.adaptive_k.enabled = False

        def _get_cfg1() -> ConfigModel:
            return cfg1

        def _get_cfg2() -> ConfigModel:
            return cfg2

        monkeypatch.setattr("autoresearch.search.core.get_config", _get_cfg1)
        results1 = s.external_lookup("python")
        assert calls == {"b1": 1, "b2": 0}
        assert s.external_lookup("python") == results1
        assert calls == {"b1": 1, "b2": 0}

        monkeypatch.setattr("autoresearch.search.core.get_config", _get_cfg2)
        results2 = s.external_lookup("python")
        assert calls == {"b1": 1, "b2": 1}
        assert s.external_lookup("python") == results2
        assert calls == {"b1": 1, "b2": 1}

        monkeypatch.setattr("autoresearch.search.core.get_config", _get_cfg1)
        assert s.external_lookup("python") == results1
        assert calls == {"b1": 1, "b2": 1}


def test_cache_key_normalizes_queries(monkeypatch: pytest.MonkeyPatch) -> None:
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

    calls: Dict[str, int] = {"count": 0}

    def backend(query: str, max_results: int = 5) -> List[Dict[str, str]]:
        calls["count"] += 1
        return [
            {
                "title": "normalized",
                "url": "https://example.com",
            }
        ]

    with search.temporary_state() as s:
        s.backends = {"dummy": backend}
        cfg = ConfigModel.model_construct(loops=1)
        cfg.search.backends = ["dummy"]
        cfg.search.context_aware.enabled = False
        cfg.search.use_semantic_similarity = False
        cfg.search.query_rewrite.enabled = False
        cfg.search.adaptive_k.enabled = False

        def _get_config() -> ConfigModel:
            return cfg

        monkeypatch.setattr("autoresearch.search.core.get_config", _get_config)

        first = s.external_lookup("  Python  ")
        second = s.external_lookup("python")
        assert calls["count"] == 1, (
            "If cache keys ignore normalization, how will repeated queries avoid redundant fetches?"
        )
        assert second == first, (
            "When normalized forms diverge, what stops the cache from fragmenting identical intents?"
        )


def test_cache_key_respects_embedding_flags(monkeypatch: pytest.MonkeyPatch) -> None:
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

    calls: Dict[str, int] = {"count": 0}

    def backend(query: str, max_results: int = 5) -> List[Dict[str, str]]:
        calls["count"] += 1
        return [{"title": "embedding", "url": "https://example.com"}]

    with search.temporary_state() as s:
        s.backends = {"dummy": backend}
        cfg = ConfigModel.model_construct(loops=1)
        cfg.search.backends = ["dummy"]
        cfg.search.context_aware.enabled = False
        cfg.search.use_semantic_similarity = True
        cfg.search.embedding_backends = []
        cfg.search.query_rewrite.enabled = False
        cfg.search.adaptive_k.enabled = False

        def _get_config() -> ConfigModel:
            return cfg

        monkeypatch.setattr("autoresearch.search.core.get_config", _get_config)

        s.external_lookup("python")
        assert calls["count"] == 1

        cfg.search.use_semantic_similarity = False
        result = s.external_lookup("python")
        assert calls["count"] == 2, (
            "If embedding toggles share cache keys, how would we detect stale similarity mixes?"
        )
        assert result[0]["title"] == "embedding"


def test_context_aware_query_expansion_uses_cache(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cache = SearchCache()
    search = Search(cache=cache)

    monkeypatch.setattr(
        Search,
        "calculate_bm25_scores",
        staticmethod(assert_bm25_signature),
    )

    calls: Dict[str, int] = {"count": 0}

    def backend(query: str, max_results: int = 5) -> List[Dict[str, str]]:
        calls["count"] += 1
        return [{"title": "Python", "url": "https://python.org"}]

    class DummyContext:
        def expand_query(self, query: str) -> str:
            return query + " expanded"

        def add_to_history(
            self, query: str, results: List[Dict[str, str]]
        ) -> None:  # pragma: no cover - no-op
            del query, results

        def build_topic_model(self) -> None:  # pragma: no cover - no-op
            return None

        def reset_search_strategy(self) -> None:  # pragma: no cover - no-op
            return None

        def summarize_retrieval_outcome(
            self,
            query: str,
            results: List[Dict[str, Any]],
            *,
            fetch_limit: int,
            by_backend: Dict[str, List[Dict[str, Any]]],
        ) -> Dict[str, Any]:  # pragma: no cover - deterministic stub
            del query, fetch_limit, by_backend
            count = len(results)
            return {
                "coverage_gap": 0.0,
                "unique_results": count,
                "result_count": count,
            }

        def record_fetch_plan(self, *args: Any, **kwargs: Any) -> None:  # pragma: no cover
            del args, kwargs

        def record_scout_observation(
            self,
            query: str,
            results: List[Dict[str, Any]],
            *,
            by_backend: Dict[str, List[Dict[str, Any]]],
        ) -> None:  # pragma: no cover - no-op
            del query, results, by_backend

    with search.temporary_state() as s:
        s.backends = {"dummy": backend}
        cfg = ConfigModel.model_construct(loops=1)
        cfg.search.backends = ["dummy"]
        cfg.search.context_aware.enabled = True
        cfg.search.context_aware.use_topic_modeling = False
        cfg.search.use_semantic_similarity = False
        cfg.search.query_rewrite.enabled = False
        cfg.search.adaptive_k.enabled = False

        def _get_config() -> ConfigModel:
            return cfg

        monkeypatch.setattr("autoresearch.search.core.get_config", _get_config)

        def _get_context() -> DummyContext:
            return DummyContext()

        monkeypatch.setattr(
            "autoresearch.search.core.SearchContext.get_instance",
            _get_context,
        )

        results1 = s.external_lookup("python")
        assert calls["count"] == 1
        results2 = s.external_lookup("python")
        assert calls["count"] == 1
        assert results2[0]["title"] == results1[0]["title"]
        assert results2[0]["url"] == results1[0]["url"]


@settings(
    max_examples=25,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
    deadline=None,
)
@given(
    st.lists(
        st.tuples(st.booleans(), st.booleans(), st.booleans()),
        min_size=1,
        max_size=6,
    )
)
def test_cache_key_property_sequences(
    monkeypatch: pytest.MonkeyPatch,
    toggle_sequence: List[Tuple[bool, bool, bool]],
) -> None:
    """Property test ensuring cache keys respect storage and hybrid toggles."""

    cache = SearchCache()
    search = Search(cache=cache)

    monkeypatch.setattr(
        Search,
        "calculate_bm25_scores",
        staticmethod(assert_bm25_signature),
    )
    monkeypatch.setattr(Search, "get_sentence_transformer", staticmethod(lambda: None))
    base_embedding = np.array([0.5, 0.25, 0.75], dtype=float)
    monkeypatch.setattr(
        Search,
        "compute_query_embedding",
        staticmethod(lambda _: base_embedding),
    )
    vector_state = {"enabled": False}
    monkeypatch.setattr(
        "autoresearch.storage.StorageManager.has_vss",
        lambda: vector_state["enabled"],
    )
    def _fake_vector_search(*_args: Any, **_kwargs: Any) -> List[Dict[str, Any]]:
        if not vector_state["enabled"]:
            return []
        return [
            {
                "node_id": "n1",
                "content": "storage snippet",
                "embedding": [0.1, 0.2],
                "similarity": 0.42,
            }
        ]

    monkeypatch.setattr(
        "autoresearch.search.storage.vector_search",
        _fake_vector_search,
    )
    monkeypatch.setattr(
        "autoresearch.storage.StorageManager.vector_search",
        staticmethod(_fake_vector_search),
    )
    monkeypatch.setattr(
        "autoresearch.search.storage.get_claim",
        lambda node_id: {"content": f"claim:{node_id}"},
    )
    monkeypatch.setattr(
        "autoresearch.storage.StorageManager.get_graph",
        lambda: None,
    )
    monkeypatch.setattr(
        "autoresearch.storage.StorageManager.query_rdf",
        lambda *_args, **_kwargs: [],
    )
    monkeypatch.setattr(
        "autoresearch.search.storage.persist_results",
        lambda *_args, **_kwargs: None,
    )

    backend_calls: Dict[str, int] = {"count": 0}
    embedding_calls: Dict[str, int] = {"count": 0}

    def backend(query: str, max_results: int = 5) -> List[Dict[str, str]]:
        backend_calls["count"] += 1
        return [
            {
                "title": f"backend-{backend_calls['count']}",
                "url": f"https://example.com/{backend_calls['count']}",
            }
        ]

    def embedding_backend(
        query_embedding: np.ndarray, max_results: int = 5
    ) -> List[Dict[str, Any]]:
        embedding_calls["count"] += 1
        return [
            {
                "title": f"embedding-{embedding_calls['count']}",
                "url": "storage://duckdb",
                "snippet": "vector",
                "embedding": query_embedding.tolist(),
            }
        ]

    with search.temporary_state() as s:
        s.backends = {"dummy": backend}
        s.embedding_backends = {"duckdb": embedding_backend}

        seen_configs: Dict[Tuple[bool, bool, bool], Tuple[Tuple[str, str], ...]] = {}

        def _result_signature(docs: List[Dict[str, Any]]) -> Tuple[Tuple[str, str], ...]:
            pairs = [(str(doc.get("url", "")), str(doc.get("title", ""))) for doc in docs]
            return tuple(sorted(pairs))

        for hybrid_enabled, semantic_enabled, vector_enabled in toggle_sequence:
            cfg = ConfigModel.model_construct(loops=1)
            cfg.search.backends = ["dummy"]
            cfg.search.embedding_backends = ["duckdb"]
            cfg.search.context_aware.enabled = False
            cfg.search.query_rewrite.enabled = False
            cfg.search.adaptive_k.enabled = False
            cfg.search.hybrid_query = hybrid_enabled
            cfg.search.use_semantic_similarity = semantic_enabled
            cfg.storage.vector_extension = vector_enabled

            vector_state["enabled"] = vector_enabled

            def _get_config(snapshot: ConfigModel = cfg) -> ConfigModel:
                return snapshot

            monkeypatch.setattr("autoresearch.search.core.get_config", _get_config)

            config_key = (hybrid_enabled, semantic_enabled, vector_enabled)
            if config_key not in seen_configs:
                prev_backend = backend_calls["count"]
                prev_embedding = embedding_calls["count"]
                first_results = s.external_lookup("python")
                assert first_results, "external_lookup should return deterministic payload"
                assert backend_calls["count"] >= prev_backend
                assert embedding_calls["count"] >= prev_embedding

                second_results = s.external_lookup("python")
                assert second_results, "cache hit should return payload"
                assert embedding_calls["count"] >= prev_embedding

                seen_configs[config_key] = _result_signature(first_results)
            else:
                prev_backend = backend_calls["count"]
                prev_embedding = embedding_calls["count"]
                cached_results = s.external_lookup("python")
                assert _result_signature(cached_results) == seen_configs[config_key]
                assert backend_calls["count"] == prev_backend
                assert embedding_calls["count"] == prev_embedding

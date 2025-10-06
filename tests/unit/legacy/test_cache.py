# mypy: ignore-errors
from __future__ import annotations

import importlib.util
from contextlib import ExitStack, contextmanager
from pathlib import Path
from threading import Thread  # for thread-safety test
from types import MethodType
from collections.abc import Callable, Iterator, Sequence
from unittest.mock import patch

import numpy as np
import pytest

if not importlib.util.find_spec("tinydb"):
    import tests.stubs.tinydb  # noqa: F401

from autoresearch.cache import SearchCache
from autoresearch.config.models import ConfigModel
from autoresearch.search import Search
from autoresearch.search.cache import build_cache_slots
from hypothesis import assume, given, settings
from hypothesis import strategies as st


SearchDocument = dict[str, object]
BackendResults = list[SearchDocument]
BackendResultMap = dict[str, BackendResults]


def assert_bm25_signature(query: str, documents: BackendResults) -> list[float]:
    """Ensure BM25 stub receives ``(query, documents)`` in that order."""
    assert isinstance(query, str)
    assert isinstance(documents, list)
    return [1.0] * len(documents)


@contextmanager
def property_search(
    cache: SearchCache,
    cfg: ConfigModel,
    *,
    embedding_vector: Sequence[float] | None = None,
    transformer_factory: Callable[[], object] | None = None,
) -> Iterator[Search]:
    """Yield a temporary :class:`Search` instance with property stubs applied."""

    with ExitStack() as stack:
        stack.enter_context(
            patch.object(
                Search,
                "calculate_bm25_scores",
                new=staticmethod(assert_bm25_signature),
            )
        )
        if embedding_vector is not None:
            vector = np.array(embedding_vector, dtype=float)

            stack.enter_context(
                patch.object(
                    Search,
                    "compute_query_embedding",
                    lambda self, _: np.array(vector, dtype=float),
                )
            )
            factory = transformer_factory or (lambda: object())
            stack.enter_context(
                patch.object(
                    Search,
                    "get_sentence_transformer",
                    new=staticmethod(lambda: factory()),
                )
            )
        else:
            stack.enter_context(
                patch.object(
                    Search,
                    "get_sentence_transformer",
                    new=staticmethod(lambda: None),
                )
            )
        stack.enter_context(
            patch("autoresearch.search.core.get_config", lambda: cfg)
        )
        search = Search(cache=cache)
        with search.temporary_state() as state:
            yield state


@pytest.fixture(autouse=True)
def _skip_ontology_reasoner(monkeypatch: pytest.MonkeyPatch) -> None:
    """Bypass heavy ontology reasoning in tests."""

    def _disable_reasoner(*_: object, **__: object) -> None:
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

    calls: dict[str, int] = {"count": 0}

    def backend(query: str, max_results: int = 5) -> list[dict[str, str]]:
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
    results: list[object] = []

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

    calls: dict[str, int] = {"b1": 0, "b2": 0}

    def backend1(query: str, max_results: int = 5) -> list[dict[str, str]]:
        calls["b1"] += 1
        return [{"title": "B1", "url": "u1"}]

    def backend2(query: str, max_results: int = 5) -> list[dict[str, str]]:
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

    calls: dict[str, int] = {"b1": 0, "b2": 0}

    def backend1(query: str, max_results: int = 5) -> list[dict[str, str]]:
        calls["b1"] += 1
        return [{"title": "B1", "url": "u1"}]

    def backend2(query: str, max_results: int = 5) -> list[dict[str, str]]:
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

    calls: dict[str, int] = {"count": 0}

    def backend(query: str, max_results: int = 5) -> list[dict[str, str]]:
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

    calls: dict[str, int] = {"count": 0}

    def backend(query: str, max_results: int = 5) -> list[dict[str, str]]:
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


@settings(max_examples=15, deadline=None)
@given(
    query=st.text(alphabet=st.characters(min_codepoint=97, max_codepoint=122), min_size=1, max_size=12),
    hybrid=st.booleans(),
    semantic=st.booleans(),
)
def test_legacy_cache_entries_upgrade_on_hit(
    query: str,
    hybrid: bool,
    semantic: bool,
) -> None:
    cache = SearchCache()

    cfg = ConfigModel.model_construct(loops=1)
    cfg.search.backends = ["legacy"]
    cfg.search.context_aware.enabled = False
    cfg.search.query_rewrite.enabled = False
    cfg.search.adaptive_k.enabled = False
    cfg.search.hybrid_query = hybrid
    cfg.search.use_semantic_similarity = semantic
    cfg.search.embedding_backends = []

    calls: dict[str, int] = {"count": 0}
    payload = [{"title": "cached", "url": "https://cached"}]
    storage_hints: tuple[str, ...] = ("external",)

    def backend(text: str, max_results: int = 5) -> list[dict[str, str]]:
        calls["count"] += 1
        return payload

    with property_search(cache, cfg) as search_default:
        search_default.backends = {"legacy": backend}
        cache_key = search_default._build_cache_key(
            backend="legacy",
            query=query,
            embedding_backends=tuple(cfg.search.embedding_backends),
            hybrid_query=cfg.search.hybrid_query,
            use_semantic_similarity=cfg.search.use_semantic_similarity,
            query_embedding=None,
            storage_hints=storage_hints,
        )
        search_default.cache.cache_results(cache_key.legacy, "legacy", payload)

        results = search_default.external_lookup(query)
        assert calls["count"] == 0, (
            "If legacy cache entries fail to migrate, why would the backend stay idle on the first hit?"
        )
        assert results, "Without cached payloads, what documents justify skipping the backend entirely?"
        assert results[0]["url"] == "https://cached"

        slots = build_cache_slots(
            cache_key,
            namespace=search_default._cache_namespace,
            embedding_backend=None,
            storage_hints=storage_hints,
        )
        assert search_default.cache.get_cached_results(slots[0], "legacy") is not None, (
            "If namespace-aware slots never fill, "
            "how will hashed entries persist for future hits?"
        )
        upgraded = search_default.cache.get_cached_results(cache_key.primary, "legacy")
        assert upgraded is not None, (
            "When migration runs, shouldn't the hashed key inherit the legacy payload for future hits?"
        )

    alt_namespace = "alt-namespace"
    with property_search(cache.namespaced(alt_namespace), cfg) as search_alt:
        search_alt.backends = {"legacy": backend}
        alt_cache_key = search_alt._build_cache_key(
            backend="legacy",
            query=query,
            embedding_backends=tuple(cfg.search.embedding_backends),
            hybrid_query=cfg.search.hybrid_query,
            use_semantic_similarity=cfg.search.use_semantic_similarity,
            query_embedding=None,
            storage_hints=storage_hints,
        )
        first = search_alt.external_lookup(query)
        assert calls["count"] == 1, (
            "If namespaces share cache slots, how would the alternate view trigger a backend fetch?"
        )
        assert first, "Without backend payloads, what documents prove the alternate namespace executed?"
        second = search_alt.external_lookup(query)
        assert calls["count"] == 1, (
            "When a namespace caches the result, shouldn't subsequent hits reuse the payload?"
        )
        assert second == first
        alt_slots = build_cache_slots(
            alt_cache_key,
            namespace=search_alt._cache_namespace,
            embedding_backend=None,
            storage_hints=storage_hints,
        )
        assert search_alt.cache.get_cached_results(alt_slots[0], "legacy") is not None, (
            "If alternate namespaces never persist slots, "
            "what guarantees their second hit avoids the backend?"
        )


@settings(max_examples=15, deadline=None)
@given(
    query=st.text(alphabet=st.characters(min_codepoint=97, max_codepoint=122), min_size=1, max_size=12),
    hybrid=st.booleans(),
    semantic=st.booleans(),
    storage_hint=st.sampled_from(["external", "embedding"]),
)
def test_v2_cache_entries_upgrade_on_hit(
    query: str,
    hybrid: bool,
    semantic: bool,
    storage_hint: str,
) -> None:
    cache = SearchCache()

    calls: dict[str, int] = {"count": 0}

    def backend(text: str, max_results: int = 5) -> list[dict[str, str]]:
        del text, max_results
        calls["count"] += 1
        return [{"title": "cached", "url": "https://cached"}]

    cfg = ConfigModel.model_construct(loops=1)
    cfg.search.backends = ["legacy"]
    cfg.search.context_aware.enabled = False
    cfg.search.query_rewrite.enabled = False
    cfg.search.adaptive_k.enabled = False
    cfg.search.hybrid_query = hybrid
    cfg.search.use_semantic_similarity = semantic
    cfg.search.embedding_backends = []

    payload = [{"title": "cached", "url": "https://cached"}]
    storage_hints: tuple[str, ...] = (storage_hint,)

    with property_search(cache, cfg) as search_default:
        search_default.backends = {"legacy": backend}
        cache_key = search_default._build_cache_key(
            backend="legacy",
            query=query,
            embedding_backends=tuple(cfg.search.embedding_backends),
            hybrid_query=cfg.search.hybrid_query,
            use_semantic_similarity=cfg.search.use_semantic_similarity,
            query_embedding=None,
            storage_hints=storage_hints,
        )

        assume(cache_key.aliases)
        alias = cache_key.aliases[0]
        search_default.cache.cache_results(alias, "legacy", payload)

        results = search_default.external_lookup(query)
        expected_calls = 0 if storage_hint == "external" else 1
        assert calls["count"] == expected_calls, (
            "If v2 cache entries failed to migrate, why would the backend fire before leveraging the alias?"
        )
        assert results, "Without cached payloads, how would the alias prove compatibility across versions?"

        repeat_default = search_default.external_lookup(query)
        assert calls["count"] == expected_calls, (
            "Once the alias migrates, why would repeated hits increment backend invocations?"
        )
        assert repeat_default == results

        slots = build_cache_slots(
            cache_key,
            namespace=search_default._cache_namespace,
            embedding_backend=None,
            storage_hints=storage_hints,
        )
        if storage_hint == "external":
            assert search_default.cache.get_cached_results(slots[0], "legacy") is not None, (
                "If alias migrations skip the namespaced slot, "
                "what ensures subsequent hits stay in-memory?"
            )
        canonical_cache_key = search_default._build_cache_key(
            backend="legacy",
            query=query,
            embedding_backends=tuple(cfg.search.embedding_backends),
            hybrid_query=cfg.search.hybrid_query,
            use_semantic_similarity=cfg.search.use_semantic_similarity,
            query_embedding=None,
            storage_hints=("external",),
        )
        canonical_slots = build_cache_slots(
            canonical_cache_key,
            namespace=search_default._cache_namespace,
            embedding_backend=None,
            storage_hints=("external",),
        )
        assert search_default.cache.get_cached_results(
            canonical_slots[0], "legacy"
        ) is not None, (
            "After migrating an alias, how could the canonical slot remain empty?"
        )
        upgraded = search_default.cache.get_cached_results(
            canonical_cache_key.primary if storage_hint != "external" else cache_key.primary,
            "legacy",
        )
        assert upgraded is not None, (
            "Once accessed via an alias, shouldn't the upgraded cache persist under the new primary hash?"
        )

    alt_namespace = "alt-v2"
    with property_search(cache.namespaced(alt_namespace), cfg) as search_alt:
        search_alt.backends = {"legacy": backend}
        alt_cache_key = search_alt._build_cache_key(
            backend="legacy",
            query=query,
            embedding_backends=tuple(cfg.search.embedding_backends),
            hybrid_query=cfg.search.hybrid_query,
            use_semantic_similarity=cfg.search.use_semantic_similarity,
            query_embedding=None,
            storage_hints=storage_hints,
        )
        baseline_calls = calls["count"]
        first = search_alt.external_lookup(query)
        assert calls["count"] == baseline_calls + 1, (
            "If alias hits leaked across namespaces, why would the alternate view touch the backend at all?"
        )
        assert first, "Without backend payloads, how would the alternate namespace prove isolation?"
        second = search_alt.external_lookup(query)
        assert calls["count"] == baseline_calls + 1, (
            "After caching per-namespace, shouldn't repeated hits fall back to the stored payload?"
        )
        assert second == first
        alt_slots = build_cache_slots(
            alt_cache_key,
            namespace=search_alt._cache_namespace,
            embedding_backend=None,
            storage_hints=storage_hints,
        )
        if storage_hint == "external":
            assert search_alt.cache.get_cached_results(alt_slots[0], "legacy") is not None, (
                "If the alternate namespace skips slot upgrades, "
                "what blocks a second backend invocation?"
            )
        canonical_alt_key = search_alt._build_cache_key(
            backend="legacy",
            query=query,
            embedding_backends=tuple(cfg.search.embedding_backends),
            hybrid_query=cfg.search.hybrid_query,
            use_semantic_similarity=cfg.search.use_semantic_similarity,
            query_embedding=None,
            storage_hints=("external",),
        )
        canonical_alt_slots = build_cache_slots(
            canonical_alt_key,
            namespace=search_alt._cache_namespace,
            embedding_backend=None,
            storage_hints=("external",),
        )
        assert search_alt.cache.get_cached_results(
            canonical_alt_slots[0], "legacy"
        ) is not None, (
            "Without canonical slot upgrades, why would the namespace avoid repeated backend calls?"
        )


@settings(max_examples=20, deadline=None)
@given(
    query=st.text(alphabet=st.characters(min_codepoint=97, max_codepoint=122), min_size=1, max_size=16),
    embedding_backends=st.lists(
        st.sampled_from(["duckdb", "faiss", "azure"]),
        unique=True,
        max_size=2,
    ),
)
def test_cache_key_primary_reflects_hybrid_flags(
    query: str,
    embedding_backends: list[str],
) -> None:
    search = Search()

    base_backends = tuple(embedding_backends)

    key_a = search._build_cache_key(
        backend="dummy",
        query=query,
        embedding_backends=base_backends,
        hybrid_query=True,
        use_semantic_similarity=False,
        query_embedding=None,
        storage_hints=("external",),
    )
    key_b = search._build_cache_key(
        backend="dummy",
        query=query,
        embedding_backends=base_backends,
        hybrid_query=False,
        use_semantic_similarity=False,
        query_embedding=None,
        storage_hints=("external",),
    )
    key_c = search._build_cache_key(
        backend="dummy",
        query=query,
        embedding_backends=base_backends,
        hybrid_query=False,
        use_semantic_similarity=True,
        query_embedding=None,
        storage_hints=("external",),
    )

    assert key_a.primary != key_b.primary, (
        "If hybrid toggles left the hash untouched, how would the cache distinguish hybrid reranks?"
    )
    assert key_b.primary != key_c.primary, (
        "When semantic similarity flips, shouldn't the cache key reflect the new retrieval plan?"
    )


@settings(max_examples=15, deadline=None)
@given(
    query=st.text(
        alphabet=st.characters(min_codepoint=97, max_codepoint=122),
        min_size=1,
        max_size=12,
    ),
    toggles=st.lists(
        st.tuples(st.booleans(), st.booleans()),
        min_size=2,
        max_size=5,
    ),
)
def test_sequential_hybrid_sequences_respect_cache_fingerprint(
    query: str,
    toggles: list[tuple[bool, bool]],
) -> None:
    cache = SearchCache()

    assume(len(set(toggles)) < len(toggles))

    calls: dict[str, int] = {"default": 0, "alt": 0}

    def backend_factory(label: str) -> Callable[[str, int], list[dict[str, str]]]:
        def _backend(q: str, max_results: int = 5) -> list[dict[str, str]]:
            del q, max_results
            calls[label] += 1
            return [{"title": "seq", "url": "https://seq"}]

        return _backend

    cfg = ConfigModel.model_construct(loops=1)
    cfg.search.backends = ["sequence"]
    cfg.search.context_aware.enabled = False
    cfg.search.query_rewrite.enabled = False
    cfg.search.adaptive_k.enabled = False
    cfg.search.embedding_backends = []

    default_fingerprints: dict[tuple[bool, bool], str] = {}
    alt_fingerprints: dict[tuple[bool, bool], str] = {}
    vector = np.array([0.2, 0.4], dtype=float)

    alt_namespace = "alt-sequence"
    with ExitStack() as stack:
        search_default = stack.enter_context(
            property_search(
                cache,
                cfg,
                embedding_vector=vector,
                transformer_factory=lambda: object(),
            )
        )
        search_alt = stack.enter_context(
            property_search(
                cache.namespaced(alt_namespace),
                cfg,
                embedding_vector=vector,
                transformer_factory=lambda: object(),
            )
        )
        search_default.backends = {"sequence": backend_factory("default")}
        search_alt.backends = {"sequence": backend_factory("alt")}

        for hybrid, semantic in toggles:
            cfg.search.hybrid_query = hybrid
            cfg.search.use_semantic_similarity = semantic

            key = (hybrid, semantic)

            prev_default = calls["default"]
            default_results = search_default.external_lookup(query)
            assert default_results, (
                "Without results, what evidence shows the cache preserved payloads?"
            )
            default_key = search_default._build_cache_key(
                backend="sequence",
                query=query,
                embedding_backends=tuple(cfg.search.embedding_backends),
                hybrid_query=hybrid,
                use_semantic_similarity=semantic,
                query_embedding=vector,
                storage_hints=("external",),
            )
            assume(default_key.fingerprint is not None)

            if key in default_fingerprints:
                assert calls["default"] == prev_default, (
                    "If cache fingerprints collide, why would sequential repeats hit the backend again?"
                )
                assert default_key.fingerprint == default_fingerprints[key], (
                    "How could identical toggle states yield differing fingerprints and still reuse cache entries?"
                )
            else:
                assert calls["default"] == prev_default + 1, (
                    "When encountering a new toggle combination, shouldn't the backend fetch occur exactly once?"
                )
                default_fingerprints[key] = default_key.fingerprint

            prev_alt = calls["alt"]
            alt_results = search_alt.external_lookup(query)
            assert alt_results == default_results, (
                "If namespaces drifted cache slots, why would the alternate view produce different results?"
            )
            alt_key = search_alt._build_cache_key(
                backend="sequence",
                query=query,
                embedding_backends=tuple(cfg.search.embedding_backends),
                hybrid_query=hybrid,
                use_semantic_similarity=semantic,
                query_embedding=vector,
                storage_hints=("external",),
            )
            assume(alt_key.fingerprint is not None)

            if key in alt_fingerprints:
                assert calls["alt"] == prev_alt, (
                    "How would cached namespaces regress if repeated draws still triggered backend calls?"
                )
                assert alt_key.fingerprint == alt_fingerprints[key], (
                    "When namespaces reuse fingerprints, shouldn't repeated hits remain stable?"
                )
            else:
                assert calls["alt"] == prev_alt + 1, (
                    "Why would a fresh namespace skip backend execution for a new toggle combination?"
                )
                alt_fingerprints[key] = alt_key.fingerprint

    assert calls["default"] == len(default_fingerprints), (
        "If caching failed, how could backend calls exceed the number of unique toggle combinations?"
    )
    assert calls["alt"] == len(alt_fingerprints), (
        "When namespaces reuse cached payloads, shouldn't backend calls still match unique combinations?"
    )


@settings(max_examples=20, deadline=None)
@given(
    vector_seed=st.booleans(),
    storage_sources=st.lists(
        st.sampled_from(["vector", "ontology", "bm25"]),
        unique=True,
        max_size=2,
    ),
)
def test_interleaved_storage_paths_share_cache(
    vector_seed: bool,
    storage_sources: list[str],
) -> None:
    cache = SearchCache()
    calls: dict[str, int] = {"backend": 0, "duckdb": 0}

    def backend(query: str, max_results: int = 5) -> list[dict[str, str]]:
        calls["backend"] += 1
        return [{"title": "primary", "url": "https://primary"}]

    def duckdb_backend(embedding: np.ndarray, max_results: int = 5) -> list[dict[str, str]]:
        del embedding, max_results
        calls["duckdb"] += 1
        return [{"title": "duckdb", "url": "https://duckdb"}]

    cfg = ConfigModel.model_construct(loops=1)
    cfg.search.backends = ["primary"]
    cfg.search.context_aware.enabled = False
    cfg.search.query_rewrite.enabled = False
    cfg.search.adaptive_k.enabled = False
    cfg.search.hybrid_query = False
    cfg.search.use_semantic_similarity = False
    cfg.search.embedding_backends = ["duckdb"]

    vector = np.array([0.1, 0.2], dtype=float)

    with ExitStack() as stack:
        stack.enter_context(
            patch(
                "autoresearch.search.core.StorageManager.has_vss",
                new=staticmethod(lambda: vector_seed),
            )
        )
        search_default = stack.enter_context(
            property_search(
                cache,
                cfg,
                embedding_vector=vector,
                transformer_factory=lambda: object(),
            )
        )

        search_default.backends = {"primary": backend}
        search_default.embedding_backends = {"duckdb": duckdb_backend}

        def fake_storage(
            self: Search,
            query: str,
            query_embedding: np.ndarray | None,
            backend_results: BackendResultMap,
            max_results: int,
        ) -> BackendResultMap:
            del self, query_embedding, backend_results, max_results
            docs: BackendResults = []
            if vector_seed:
                docs.append(
                    {
                        "url": "urn:vector",
                        "title": "VectorDoc",
                        "storage_sources": ["vector"],
                    }
                )
            for source in storage_sources:
                if source == "vector" and not vector_seed:
                    continue
                docs.append(
                    {
                        "url": f"urn:{source}",
                        "title": f"{source.title()}Doc",
                        "storage_sources": [source],
                    }
                )
            return {"storage": docs}

        search_default.storage_hybrid_lookup = MethodType(fake_storage, search_default)

        first = search_default.external_lookup("topic")
        initial_backend_calls = calls["backend"]
        initial_duckdb_calls = calls["duckdb"]
        second = search_default.external_lookup("topic")

        assert calls["backend"] == initial_backend_calls, (
            "If storage interleaving broke cache hashes, why didn't the backend fire twice?"
        )
        assert calls["duckdb"] == initial_duckdb_calls, (
            "When duckdb seeds vary, shouldn't cached embeddings prevent duplicate vector fetches?"
        )
        assert second == first, (
            "Without stable cache keys, how could sequential storage blends return identical payloads?"
        )

        key = search_default._build_cache_key(
            backend="primary",
            query="topic",
            embedding_backends=tuple(cfg.search.embedding_backends),
            hybrid_query=cfg.search.hybrid_query,
            use_semantic_similarity=cfg.search.use_semantic_similarity,
            query_embedding=vector,
            storage_hints=("external",),
        )
        assume(key.fingerprint is not None)
        repeat = search_default._build_cache_key(
            backend="primary",
            query="topic",
            embedding_backends=tuple(cfg.search.embedding_backends),
            hybrid_query=cfg.search.hybrid_query,
            use_semantic_similarity=cfg.search.use_semantic_similarity,
            query_embedding=vector,
            storage_hints=("external",),
        )
        assert repeat.fingerprint == key.fingerprint, (
            "If interleaved storage altered the fingerprint, what mechanism would keep cache hits deterministic?"
        )

    assert calls["backend"] == 1, (
        "If cache slots multiplied, how could backend calls stay capped at a single execution?"
    )
    assert calls["duckdb"] <= 1, (
        "When cache keys stabilise embeddings, shouldn't vector fetches avoid repeated calls?"
    )


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

    calls: dict[str, int] = {"count": 0}

    def backend(query: str, max_results: int = 5) -> list[dict[str, str]]:
        calls["count"] += 1
        return [{"title": "Python", "url": "https://python.org"}]

    class DummyContext:
        def expand_query(self, query: str) -> str:
            return query + " expanded"

        def add_to_history(
            self, query: str, results: list[dict[str, str]]
        ) -> None:  # pragma: no cover - no-op
            del query, results

        def build_topic_model(self) -> None:  # pragma: no cover - no-op
            return None

        def reset_search_strategy(self) -> None:  # pragma: no cover - no-op
            return None

        def summarize_retrieval_outcome(
            self,
            query: str,
            results: BackendResults,
            *,
            fetch_limit: int,
            by_backend: BackendResultMap,
        ) -> dict[str, object]:  # pragma: no cover - deterministic stub
            del query, fetch_limit, by_backend
            count = len(results)
            return {
                "coverage_gap": 0.0,
                "unique_results": count,
                "result_count": count,
            }

        def record_fetch_plan(self, *args: object, **kwargs: object) -> None:  # pragma: no cover
            del args, kwargs

        def record_scout_observation(
            self,
            query: str,
            results: BackendResults,
            *,
            by_backend: BackendResultMap,
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

from __future__ import annotations

import pytest

from autoresearch.config.models import (
    AdaptiveKConfig,
    ConfigModel,
    ContextAwareSearchConfig,
    QueryRewriteConfig,
    SearchConfig,
)
from autoresearch.search.core import Search
from autoresearch.search.context import SearchContext


def _build_config(
    *,
    backends: list[str],
    max_results: int,
    rewrite_cfg: QueryRewriteConfig,
    adaptive_cfg: AdaptiveKConfig,
    capture_strategy: bool = True,
    capture_critique: bool = True,
) -> ConfigModel:
    base = ConfigModel()
    search_cfg = SearchConfig(
        backends=backends,
        embedding_backends=[],
        max_results_per_query=max_results,
        hybrid_query=False,
        use_semantic_similarity=False,
        use_bm25=False,
        use_source_credibility=False,
        semantic_similarity_weight=1.0,
        bm25_weight=0.0,
        source_credibility_weight=0.0,
        use_feedback=False,
        feedback_weight=0.0,
        context_aware=ContextAwareSearchConfig(enabled=False),
        query_rewrite=rewrite_cfg,
        adaptive_k=adaptive_cfg,
    )
    return base.model_copy(
        update={
            "search": search_cfg,
            "gate_capture_query_strategy": capture_strategy,
            "gate_capture_self_critique": capture_critique,
        }
    )


@pytest.fixture
def isolated_search(monkeypatch: pytest.MonkeyPatch) -> Search:
    """Return a fresh Search instance with storage side effects disabled."""

    class _StorageStub:
        @staticmethod
        def has_vss() -> bool:
            return False

    monkeypatch.setattr(
        "autoresearch.search.core.search_storage.persist_results",
        lambda results: None,
    )
    monkeypatch.setattr("autoresearch.search.core.StorageManager", _StorageStub)
    monkeypatch.setattr(
        "autoresearch.search.core.SearchCache.get_cached_results",
        lambda self, query, backend: None,
    )
    monkeypatch.setattr(
        "autoresearch.search.core.SearchCache.cache_results",
        lambda self, query, backend, results: None,
    )
    search = Search()
    return search


def test_external_lookup_triggers_query_rewrite(
    monkeypatch: pytest.MonkeyPatch, isolated_search: Search
) -> None:
    config = _build_config(
        backends=["stub"],
        max_results=2,
        rewrite_cfg=QueryRewriteConfig(
            enabled=True,
            max_attempts=1,
            min_results=2,
            min_unique_sources=2,
            coverage_gap_threshold=0.1,
        ),
        adaptive_cfg=AdaptiveKConfig(enabled=False),
    )
    monkeypatch.setattr("autoresearch.search.core.get_config", lambda: config)
    monkeypatch.setattr("autoresearch.search.context.get_config", lambda: config)

    calls: list[tuple[str, int]] = []

    def backend(query: str, max_results: int) -> list[dict[str, str]]:
        calls.append((query, max_results))
        if query == "alpha":
            return [{"title": "alpha", "url": "1"}]
        if query == "alpha rewrite":
            return [
                {"title": f"alpha-{i}", "url": str(i)} for i in range(max_results)
            ]
        return []

    isolated_search.backends = {"stub": backend}
    monkeypatch.setattr(
        SearchContext,
        "suggest_rewrites",
        lambda self, query, limit=3: [
            {"query": "alpha rewrite", "reason": "test"}
        ],
    )

    with SearchContext.temporary_instance():
        results = isolated_search.external_lookup("alpha", max_results=2)
        assert len(results) == 2
        assert calls
        assert calls[0] == ("alpha", 2)
        assert all(call[1] == 2 for call in calls)
        rewritten_queries = [query for query, _ in calls[1:]]
        assert rewritten_queries
        assert all(query != "" for query in rewritten_queries)
        assert any(query != "alpha" for query in rewritten_queries)

        strategy = SearchContext.get_instance().get_search_strategy()
        rewrites = strategy.get("rewrites") or []
        assert rewrites
        rewrite_targets = [entry.get("to") for entry in rewrites if entry.get("to")]
        assert any(target in rewritten_queries for target in rewrite_targets)

        attempts = strategy.get("fetch_plan", {}).get("attempts", [])
        assert len(attempts) >= max(2, len(calls))
        assert all(entry.get("k") == 2 for entry in attempts[: len(calls)])

        markers = SearchContext.get_instance().get_self_critique_markers()
        assert markers.get("coverage_gap", 0.0) > 0.0


def test_external_lookup_adaptive_k_increases_fetch(
    monkeypatch: pytest.MonkeyPatch, isolated_search: Search
) -> None:
    config = _build_config(
        backends=["stub"],
        max_results=2,
        rewrite_cfg=QueryRewriteConfig(enabled=False),
        adaptive_cfg=AdaptiveKConfig(
            enabled=True,
            min_k=2,
            max_k=4,
            step=2,
            coverage_gap_threshold=0.25,
        ),
    )
    monkeypatch.setattr("autoresearch.search.core.get_config", lambda: config)
    monkeypatch.setattr("autoresearch.search.context.get_config", lambda: config)

    calls: list[tuple[str, int]] = []

    def backend(query: str, max_results: int) -> list[dict[str, str]]:
        calls.append((query, max_results))
        if max_results <= 2:
            return [{"title": "alpha", "url": "1"}]
        return [
            {"title": f"alpha-{i}", "url": str(i)} for i in range(max_results)
        ]

    isolated_search.backends = {"stub": backend}

    with SearchContext.temporary_instance():
        results = isolated_search.external_lookup("adaptive", max_results=2)
        assert len(results) == 4
        assert calls == [("adaptive", 2), ("adaptive", 4)]
        strategy = SearchContext.get_instance().get_search_strategy()
        attempts = strategy.get("fetch_plan", {}).get("attempts", [])
        assert [entry["k"] for entry in attempts] == [2, 4]
        rewrites = strategy.get("rewrites", [])
        assert not rewrites


def test_query_strategy_markers_disabled(
    monkeypatch: pytest.MonkeyPatch, isolated_search: Search
) -> None:
    config = _build_config(
        backends=["stub"],
        max_results=2,
        rewrite_cfg=QueryRewriteConfig(
            enabled=True,
            max_attempts=1,
            min_results=2,
            min_unique_sources=2,
            coverage_gap_threshold=0.1,
        ),
        adaptive_cfg=AdaptiveKConfig(enabled=False),
        capture_strategy=False,
    )
    monkeypatch.setattr("autoresearch.search.core.get_config", lambda: config)
    monkeypatch.setattr("autoresearch.search.context.get_config", lambda: config)

    def backend(query: str, max_results: int) -> list[dict[str, str]]:
        return [{"title": "alpha", "url": "1"}]

    isolated_search.backends = {"stub": backend}

    with SearchContext.temporary_instance():
        results = isolated_search.external_lookup("alpha", max_results=2)
        assert results
        strategy = SearchContext.get_instance().get_search_strategy()
        assert strategy == {}


def test_self_critique_markers_disabled(
    monkeypatch: pytest.MonkeyPatch, isolated_search: Search
) -> None:
    config = _build_config(
        backends=["stub"],
        max_results=2,
        rewrite_cfg=QueryRewriteConfig(
            enabled=True,
            max_attempts=1,
            min_results=2,
            min_unique_sources=2,
            coverage_gap_threshold=0.1,
        ),
        adaptive_cfg=AdaptiveKConfig(enabled=False),
        capture_critique=False,
    )
    monkeypatch.setattr("autoresearch.search.core.get_config", lambda: config)
    monkeypatch.setattr("autoresearch.search.context.get_config", lambda: config)

    def backend(query: str, max_results: int) -> list[dict[str, str]]:
        return [{"title": "alpha", "url": "1"}]

    isolated_search.backends = {"stub": backend}

    with SearchContext.temporary_instance():
        results = isolated_search.external_lookup("alpha", max_results=2)
        assert results
        markers = SearchContext.get_instance().get_self_critique_markers()
        assert markers == {}

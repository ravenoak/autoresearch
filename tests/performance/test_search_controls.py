"""Performance regressions for search caching and parallel toggles."""

from __future__ import annotations

from types import SimpleNamespace
from typing import Dict, List

import pytest

from autoresearch.cache import SearchCache
from autoresearch.search.core import Search


def _make_runtime_config(*, shared: bool, parallel: bool) -> SimpleNamespace:
    """Return a minimal runtime config satisfying the search protocol."""

    search = SimpleNamespace(
        backends=["stub"],
        embedding_backends=[],
        hybrid_query=False,
        use_semantic_similarity=False,
        use_bm25=False,
        use_source_credibility=False,
        bm25_weight=0.0,
        semantic_similarity_weight=0.0,
        source_credibility_weight=0.0,
        max_workers=2,
        shared_retrieval_cache=shared,
        parallel_backends=parallel,
        context_aware=SimpleNamespace(enabled=False, use_topic_modeling=False),
        local_file=SimpleNamespace(path="", file_types=["txt"]),
        local_git=SimpleNamespace(repo_path="", branches=["main"], history_depth=10),
    )
    return SimpleNamespace(search=search)


@pytest.fixture(autouse=True)
def _reset_shared_cache() -> None:
    """Ensure shared caches do not leak across test cases."""

    Search._clear_shared_caches()


def test_shared_retrieval_cache_reuses_backend(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    """Shared in-memory caches avoid repeated backend execution."""

    calls: List[str] = []

    def stub_backend(query: str, limit: int) -> List[Dict[str, str]]:
        calls.append(query)
        return [{"title": query, "url": f"https://example.com/{len(calls)}"}]

    config = _make_runtime_config(shared=True, parallel=True)
    monkeypatch.setattr("autoresearch.search.core.get_config", lambda: config)
    cache = SearchCache(str(tmp_path / "cache.json"))
    search = Search(cache=cache)

    with search.temporary_state() as temp:
        temp.backends = {"stub": stub_backend}
        temp.embedding_backends = {}
        temp.cache.clear()

        temp.external_lookup("dialectics", max_results=3)
        assert len(calls) == 1

        temp.cache.clear()
        temp.external_lookup("dialectics", max_results=3)
        assert len(calls) == 1, "shared cache should prevent a second backend call"


def test_parallel_toggle_disables_threadpool(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    """Disabling parallel backends avoids ThreadPoolExecutor usage."""

    calls: List[str] = []

    def stub_backend(query: str, limit: int) -> List[Dict[str, str]]:
        calls.append(query)
        return [{"title": query, "url": "https://example.com"}]

    config = _make_runtime_config(shared=True, parallel=False)
    monkeypatch.setattr("autoresearch.search.core.get_config", lambda: config)

    def _failing_executor(*args, **kwargs):
        raise AssertionError("ThreadPoolExecutor should not be constructed when parallelism is disabled")

    monkeypatch.setattr("autoresearch.search.core.ThreadPoolExecutor", _failing_executor)

    cache = SearchCache(str(tmp_path / "cache2.json"))
    search = Search(cache=cache)

    with search.temporary_state() as temp:
        temp.backends = {"stub": stub_backend}
        temp.embedding_backends = {}
        temp.cache.clear()
        temp.external_lookup("budget", max_results=2)

    assert calls == ["budget"]

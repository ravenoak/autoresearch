"""Performance regression tests for search parallelisation controls."""

from __future__ import annotations

import time
from typing import Dict, List

from autoresearch.config.loader import ConfigLoader
from autoresearch.config.models import ConfigModel
from autoresearch.search.core import Search


def _configure_search(parallel_enabled: bool, parallel_prefetch: int = 0) -> ConfigModel:
    config = ConfigModel()
    config.search.backends = ["slow", "fast"]
    config.search.parallel_enabled = parallel_enabled
    config.search.parallel_prefetch = parallel_prefetch
    config.search.shared_cache = False
    config.search.cache_namespace = "test"
    return config


def test_external_lookup_runs_sequentially_when_parallel_disabled() -> None:
    """Disabling parallel execution should process backends sequentially."""

    config = _configure_search(parallel_enabled=False)
    order: List[str] = []

    with ConfigLoader.temporary_instance(search_paths=[]) as loader:
        loader._config = config
        search = Search()

        def slow_backend(query: str, max_results: int) -> List[Dict[str, str]]:
            order.append("slow")
            time.sleep(0.05)
            return [{"title": "slow", "url": ""}]

        def fast_backend(query: str, max_results: int) -> List[Dict[str, str]]:
            order.append("fast")
            time.sleep(0.05)
            return [{"title": "fast", "url": ""}]

        search.backends = {"slow": slow_backend, "fast": fast_backend}

        start = time.perf_counter()
        search.external_lookup("query", max_results=1)
        elapsed = time.perf_counter() - start
        search.reset()

    assert order == ["slow", "fast"]
    assert elapsed >= 0.09


def test_external_lookup_fans_out_when_parallel_enabled() -> None:
    """Parallel lookups should overlap backend latency to reduce wall time."""

    config = _configure_search(parallel_enabled=True, parallel_prefetch=0)
    order: List[str] = []

    with ConfigLoader.temporary_instance(search_paths=[]) as loader:
        loader._config = config
        search = Search()

        def slow_backend(query: str, max_results: int) -> List[Dict[str, str]]:
            order.append("slow")
            time.sleep(0.05)
            return [{"title": "slow", "url": ""}]

        def fast_backend(query: str, max_results: int) -> List[Dict[str, str]]:
            order.append("fast")
            time.sleep(0.05)
            return [{"title": "fast", "url": ""}]

        search.backends = {"slow": slow_backend, "fast": fast_backend}

        start = time.perf_counter()
        search.external_lookup("query", max_results=1)
        elapsed = time.perf_counter() - start
        search.reset()

    assert set(order) == {"slow", "fast"}
    assert elapsed < 0.09

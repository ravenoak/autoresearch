"""Regression test for search results stability."""

from __future__ import annotations

from collections.abc import Callable
from typing import Mapping, Sequence

import pytest

from autoresearch.config.models import ConfigModel
from autoresearch.search import Search


SearchResults = Sequence[Mapping[str, object]]


def test_search_results_stable(
    monkeypatch: pytest.MonkeyPatch,
    search_baseline: Callable[[SearchResults], None],
) -> None:
    """Search results remain stable across releases."""

    def backend(query: str, max_results: int = 5) -> SearchResults:
        return [{"title": "example", "url": "https://example.com"}]

    monkeypatch.setitem(Search.backends, "dummy", backend)
    cfg = ConfigModel(loops=1)
    cfg.search.backends = ["dummy"]
    cfg.search.context_aware.enabled = False
    monkeypatch.setattr("autoresearch.search.core.get_config", lambda: cfg)

    results: SearchResults = Search.external_lookup("example")
    search_baseline(results)

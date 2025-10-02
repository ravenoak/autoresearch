from pytest_bdd import parsers, scenario, then, when
from __future__ import annotations

from pathlib import Path
from typing import Any, cast

import pytest
from pytest_bdd import parsers, scenario, then, when

from autoresearch.config.models import ConfigModel
from autoresearch.search import Search
from tests.behavior.context import BehaviorContext


@scenario("../features/hybrid_search.feature", "Combine keyword and vector results")
def test_hybrid_search() -> None:
    """Hybrid search mixes vector and keyword results."""
    pass


@when(parsers.parse('I perform a hybrid search for "{query}"'))
def perform_hybrid_search(
    query: str,
    monkeypatch: pytest.MonkeyPatch,
    bdd_context: BehaviorContext,
) -> None:
    cfg = ConfigModel(loops=1)
    cfg.search.backends = ["local_file"]
    cfg.search.embedding_backends = ["duckdb"]
    cfg.search.hybrid_query = True
    cfg.search.context_aware.enabled = False
    docs_dir_obj = bdd_context.get("docs_dir")
    if not isinstance(docs_dir_obj, Path):
        raise TypeError("docs_dir must be a Path in behavior context")
    cfg.search.local_file.path = str(docs_dir_obj)
    cfg.search.local_file.file_types = ["txt"]
    monkeypatch.setattr("autoresearch.search.core.get_config", lambda: cfg)
    hybrid_results = cast(
        list[dict[str, Any]], Search.external_lookup(query, max_results=5)
    )
    bdd_context["search_results"] = hybrid_results
    bdd_context["hybrid_results"] = hybrid_results
    cfg_sem = cfg.model_copy(deep=True)
    cfg_sem.search.hybrid_query = False
    monkeypatch.setattr("autoresearch.search.core.get_config", lambda: cfg_sem)
    semantic_results = cast(
        list[dict[str, Any]], Search.external_lookup(query, max_results=5)
    )
    bdd_context["semantic_results"] = semantic_results
    monkeypatch.setattr("autoresearch.search.core.get_config", lambda: cfg)


@then("the search results should include vector results")
def check_vector_results(bdd_context: BehaviorContext) -> None:
    results = cast(list[dict[str, Any]], bdd_context["search_results"])
    assert any("embedding" in r for r in results)


@then("the first result should match the semantic search ordering")
def first_result_matches_semantic(bdd_context: BehaviorContext) -> None:
    hybrid = cast(list[dict[str, Any]], bdd_context["hybrid_results"])[0]
    semantic = cast(list[dict[str, Any]], bdd_context["semantic_results"])[0]
    assert hybrid["url"] == semantic["url"]


@then("the relevance scores should be normalized")
def relevance_scores_normalized(bdd_context: BehaviorContext) -> None:
    hybrid_results = cast(list[dict[str, Any]], bdd_context["hybrid_results"])
    scores = [float(r["relevance_score"]) for r in hybrid_results]
    assert all(0.0 <= s <= 1.0 for s in scores)
    assert scores == sorted(scores, reverse=True)

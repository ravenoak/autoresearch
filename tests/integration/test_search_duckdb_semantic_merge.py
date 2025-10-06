# mypy: ignore-errors
from typing import Mapping, Sequence

import pytest

from autoresearch.config import ConfigModel, SearchConfig
from autoresearch.config.loader import ConfigLoader
from autoresearch.search.core import Search

SearchResults = Sequence[Mapping[str, object]]


def _config(monkeypatch: pytest.MonkeyPatch) -> None:
    cfg = ConfigModel(
        search=SearchConfig(
            bm25_weight=0.0,
            semantic_similarity_weight=1.0,
            source_credibility_weight=0.0,
            use_bm25=False,
            use_source_credibility=False,
            use_semantic_similarity=True,
        )
    )
    ConfigLoader.reset_instance()

    def load_config_override(self: ConfigLoader) -> ConfigModel:
        return cfg

    monkeypatch.setattr(ConfigLoader, "load_config", load_config_override)


def test_semantic_scores_ignore_zero_vectors(monkeypatch: pytest.MonkeyPatch) -> None:
    _config(monkeypatch)
    results: list[Mapping[str, object]] = [
        {"title": "a", "similarity": 0.0},
        {"title": "b", "similarity": 0.0},
    ]

    def _semantic_similarity(
        self: Search,
        query: str,
        docs: SearchResults,
        query_embedding: Sequence[float] | None = None,
    ) -> Sequence[float]:
        return [0.9, 0.1]

    monkeypatch.setattr(Search, "calculate_semantic_similarity", _semantic_similarity)
    ranked: SearchResults = Search.rank_results("q", results)
    assert [r["title"] for r in ranked] == ["a", "b"]
    assert ranked[0]["relevance_score"] == 1.0
    assert ranked[1]["relevance_score"] < 0.2

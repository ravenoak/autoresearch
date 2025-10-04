"""Verify hybrid ranking scores are normalized."""

from typing import Mapping, Sequence

import pytest

from autoresearch.config import ConfigModel, SearchConfig
from autoresearch.config.loader import ConfigLoader
from autoresearch.search.core import Search

SearchResults = Sequence[Mapping[str, object]]


def _config(monkeypatch: pytest.MonkeyPatch) -> None:
    cfg = ConfigModel(search=SearchConfig())
    ConfigLoader.reset_instance()

    def load_config_override(self: ConfigLoader) -> ConfigModel:
        return cfg

    monkeypatch.setattr(ConfigLoader, "load_config", load_config_override)


def test_rank_results_normalizes_scores(monkeypatch: pytest.MonkeyPatch) -> None:
    """Scores are scaled to the unit interval."""
    _config(monkeypatch)
    results: list[Mapping[str, object]] = [
        {"title": "a", "similarity": 2.0},
        {"title": "b", "similarity": 0.5},
    ]
    ranked: SearchResults = Search.rank_results("test", results)
    scores: list[float] = [float(r["relevance_score"]) for r in ranked]
    assert all(0 <= s <= 1 for s in scores)
    assert scores[0] == 1.0

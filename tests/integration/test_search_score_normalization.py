"""Verify hybrid ranking scores are normalized."""

from autoresearch.config import ConfigModel, SearchConfig
from autoresearch.config.loader import ConfigLoader
from autoresearch.search.core import Search


def _config(monkeypatch) -> None:
    cfg = ConfigModel(search=SearchConfig())
    ConfigLoader.reset_instance()
    monkeypatch.setattr(ConfigLoader, "load_config", lambda self: cfg)


def test_rank_results_normalizes_scores(monkeypatch) -> None:
    """Scores are scaled to the unit interval."""
    _config(monkeypatch)
    results = [
        {"title": "a", "similarity": 2.0},
        {"title": "b", "similarity": 0.5},
    ]
    ranked = Search.rank_results("test", results)
    scores = [r["relevance_score"] for r in ranked]
    assert all(0 <= s <= 1 for s in scores)
    assert scores[0] == 1.0

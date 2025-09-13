import pytest

from autoresearch.search.ranking import combine_scores
from autoresearch.search.core import Search
from autoresearch.config import ConfigModel
from autoresearch.config.models import SearchConfig
from autoresearch.config.loader import ConfigLoader


def test_combine_scores_weighted_sum() -> None:
    """combine_scores applies weights after normalizing components."""
    bm25 = [3.0, 1.0]
    semantic = [0.8, 0.2]
    credibility = [0.9, 0.5]
    weights = (0.5, 0.3, 0.2)
    scores = combine_scores(bm25, semantic, credibility, weights)
    assert scores == pytest.approx([1.0, 0.35], abs=0.01)
    assert all(0.0 <= s <= 1.0 for s in scores)


def test_combine_scores_invalid_weights() -> None:
    """Invalid weight sums raise ValueError."""
    with pytest.raises(ValueError):
        combine_scores([1.0], [1.0], [1.0], (0.6, 0.3, 0.2))


def test_duckdb_scores_used_without_semantic(monkeypatch) -> None:
    """DuckDB similarities act as semantic component when semantic search is off."""
    cfg = ConfigModel(search=SearchConfig(use_semantic_similarity=False))
    ConfigLoader.reset_instance()
    monkeypatch.setattr(ConfigLoader, "load_config", lambda self: cfg)
    monkeypatch.setattr(Search, "calculate_bm25_scores", staticmethod(lambda q, r: [0.0, 0.0]))
    monkeypatch.setattr(Search, "assess_source_credibility", lambda self, r: [0.0, 0.0])
    docs = [
        {"title": "a", "similarity": 0.2},
        {"title": "b", "similarity": 0.8},
    ]
    ranked = Search.rank_results("q", docs)
    assert [d["title"] for d in ranked] == ["b", "a"]

import pytest

from autoresearch.config import ConfigModel
from autoresearch.config.loader import ConfigLoader
from autoresearch.config.models import SearchConfig
from autoresearch.search.core import Search
from autoresearch.search.ranking import combine_scores


def test_combine_scores_weighted_sum() -> None:
    """combine_scores applies weights after normalizing components."""
    bm25 = [3.0, 1.0]
    semantic = [0.8, 0.2]
    credibility = [0.9, 0.5]
    weights = (0.5, 0.3, 0.2)
    scores = combine_scores(bm25, semantic, credibility, weights)
    assert scores == pytest.approx([1.0, 0.0], abs=0.01)
    assert all(0.0 <= s <= 1.0 for s in scores)


def test_combine_scores_requires_convex_weights() -> None:
    """Weights must be non-negative and sum to one."""
    bm25 = [3.0]
    semantic = [0.8]
    credibility = [0.9]
    with pytest.raises(ValueError):
        combine_scores(bm25, semantic, credibility, (0.5, 0.25, 0.1))
    with pytest.raises(ValueError):
        combine_scores(bm25, semantic, credibility, (-0.1, 0.6, 0.5))


def test_duckdb_scores_used_without_semantic(monkeypatch) -> None:
    """DuckDB similarities rank results when semantic search is disabled."""
    cfg = ConfigModel(
        search=SearchConfig(
            use_semantic_similarity=False,
            use_bm25=False,
            use_source_credibility=False,
        )
    )
    ConfigLoader.reset_instance()
    monkeypatch.setattr(ConfigLoader, "load_config", lambda self: cfg)
    docs = [
        {"title": "a", "similarity": 0.2},
        {"title": "b", "similarity": 0.8},
    ]
    ranked = Search.rank_results("q", docs)
    assert [d["title"] for d in ranked] == ["b", "a"]
    assert ranked[0]["bm25_score"] == ranked[0]["credibility_score"] == 1.0


def test_rank_results_weighted_combination(monkeypatch) -> None:
    """Search.rank_results normalizes and respects component weights."""
    cfg = ConfigModel(
        search=SearchConfig(
            bm25_weight=2.0,
            semantic_similarity_weight=8.0,
            source_credibility_weight=0.0,
        )
    )
    ConfigLoader.reset_instance()
    monkeypatch.setattr(ConfigLoader, "load_config", lambda self: cfg)
    monkeypatch.setattr(
        Search,
        "calculate_bm25_scores",
        staticmethod(lambda q, r: [0.1, 0.9]),
    )
    monkeypatch.setattr(
        Search,
        "calculate_semantic_similarity",
        lambda self, q, r, e=None: [0.9, 0.1],
    )
    monkeypatch.setattr(
        Search,
        "assess_source_credibility",
        lambda self, r: [1.0, 1.0],
    )
    docs = [{"title": "a"}, {"title": "b"}]
    ranked = Search.rank_results("q", docs)
    assert [d["title"] for d in ranked] == ["a", "b"]


def test_rank_results_weight_fallback(monkeypatch) -> None:
    """Zero weights fall back to equal weighting across enabled components."""
    cfg = ConfigModel(
        search=SearchConfig(
            bm25_weight=0.0,
            semantic_similarity_weight=0.0,
            source_credibility_weight=0.0,
            use_bm25=True,
            use_semantic_similarity=True,
            use_source_credibility=True,
        )
    )
    ConfigLoader.reset_instance()
    monkeypatch.setattr(ConfigLoader, "load_config", lambda self: cfg)
    monkeypatch.setattr(
        Search,
        "calculate_bm25_scores",
        staticmethod(lambda q, r: [0.9, 0.1]),
    )
    monkeypatch.setattr(
        Search,
        "calculate_semantic_similarity",
        lambda self, q, r, e=None: [0.9, 0.1],
    )
    monkeypatch.setattr(
        Search,
        "assess_source_credibility",
        lambda self, r: [0.9, 0.1],
    )
    docs = [{"title": "a"}, {"title": "b"}]
    ranked = Search.rank_results("q", docs)
    assert [d["title"] for d in ranked] == ["a", "b"]

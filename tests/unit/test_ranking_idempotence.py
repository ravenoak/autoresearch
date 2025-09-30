from autoresearch.config.loader import ConfigLoader
from autoresearch.config.models import ConfigModel, SearchConfig
from autoresearch.search.core import RANKING_BUCKET_SCALE, Search
import pytest


def _setup(monkeypatch) -> None:
    cfg = ConfigModel(
        search=SearchConfig(
            bm25_weight=0.5,
            semantic_similarity_weight=0.3,
            source_credibility_weight=0.2,
        )
    )
    monkeypatch.setattr(ConfigLoader, "load_config", lambda self: cfg)
    ConfigLoader()._config = None
    monkeypatch.setattr(Search, "calculate_bm25_scores", staticmethod(lambda q, r: [0.2, 0.1]))
    monkeypatch.setattr(
        Search,
        "calculate_semantic_similarity",
        lambda self, q, r, query_embedding=None: [0.3, 0.4],
    )
    monkeypatch.setattr(Search, "assess_source_credibility", lambda self, r: [0.5, 0.6])


def test_rank_results_idempotent(monkeypatch: pytest.MonkeyPatch) -> None:
    """Ranking twice matches docs/algorithms/relevance_ranking.md coverage."""
    results = [
        {"title": "a", "url": "https://a"},
        {"title": "b", "url": "https://b"},
    ]
    _setup(monkeypatch)
    ranked = Search.rank_results("q", results)
    reranked = Search.rank_results("q", ranked)
    assert [r["url"] for r in ranked] == [r["url"] for r in reranked]
    assert [r["relevance_bucket"] for r in ranked] == [
        r["relevance_bucket"] for r in reranked
    ]
    assert [r["raw_relevance_bucket"] for r in ranked] == [
        r["raw_relevance_bucket"] for r in reranked
    ]
    for first, second in zip(ranked, reranked, strict=True):
        assert first["relevance_bucket"] == int(
            round(first["relevance_score"] * RANKING_BUCKET_SCALE)
        )
        assert second["relevance_bucket"] == int(
            round(second["relevance_score"] * RANKING_BUCKET_SCALE)
        )
        assert first["raw_relevance_bucket"] == int(
            round(first["raw_merged_score"] * RANKING_BUCKET_SCALE)
        )
        assert second["raw_relevance_bucket"] == int(
            round(second["raw_merged_score"] * RANKING_BUCKET_SCALE)
        )

"""Tests for source credibility scoring logic."""

from unittest.mock import MagicMock, patch

from autoresearch.config.models import SearchConfig
from autoresearch.search import Search


def test_assess_source_credibility_partial_domains():
    docs = [
        {"url": "https://dept.university.edu/paper"},
        {"url": "https://agency.gov/report"},
        {"url": "https://unknown.io/post"},
    ]
    scores = Search.assess_source_credibility(docs)
    assert scores == [0.8, 0.85, 0.5]


def test_rank_results_prefers_higher_credibility():
    docs = [
        {"url": "https://dept.university.edu/paper"},
        {"url": "https://unknown.io/post"},
    ]
    cfg = MagicMock()
    cfg.search = SearchConfig(
        use_bm25=True,
        use_semantic_similarity=True,
        use_source_credibility=True,
        bm25_weight=0.0,
        semantic_similarity_weight=0.0,
        source_credibility_weight=1.0,
    )
    with (
        patch("autoresearch.search.core.get_config", return_value=cfg),
        patch.object(Search, "calculate_bm25_scores", return_value=[0.5, 0.5]),
        patch.object(
            Search, "calculate_semantic_similarity", return_value=[0.5, 0.5]
        ),
    ):
        ranked = Search.rank_results("query", docs)
    assert [r["url"] for r in ranked] == [
        "https://dept.university.edu/paper",
        "https://unknown.io/post",
    ]

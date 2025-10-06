# mypy: ignore-errors
from __future__ import annotations

import copy
from typing import List

import pytest
from hypothesis import assume, given, strategies as st

from autoresearch.config.loader import ConfigLoader
from autoresearch.config.models import ConfigModel, SearchConfig
from autoresearch.search import Search
from autoresearch.search.core import RANKING_BUCKET_SCALE
from autoresearch.search.ranking_formula import combine_scores


@given(
    bm25_scores=st.lists(st.floats(min_value=0, max_value=1), min_size=1, max_size=5),
    semantic_scores=st.lists(st.floats(min_value=0, max_value=1), min_size=1, max_size=5),
    w1=st.floats(min_value=0, max_value=1),
    w2=st.floats(min_value=0, max_value=1),
)
def test_merge_rank_scores_linear(
    bm25_scores: List[float],
    semantic_scores: List[float],
    w1: float,
    w2: float,
) -> None:
    """BM25 and semantic scores combine linearly.

    References: docs/algorithms/bm25.md, docs/algorithms/semantic_similarity.md
    """
    merged = Search.merge_rank_scores(bm25_scores, semantic_scores, w1, w2)
    expected_len = min(len(bm25_scores), len(semantic_scores))
    assert len(merged) == expected_len
    for i in range(expected_len):
        assert merged[i] == bm25_scores[i] * w1 + semantic_scores[i] * w2


def configure_ranker(
    monkeypatch: pytest.MonkeyPatch,
    weights: List[float],
    bm25_scores: List[float],
    semantic_scores: List[float],
    credibility_scores: List[float],
) -> None:
    cfg = ConfigModel(
        search=SearchConfig(
            bm25_weight=weights[0],
            semantic_similarity_weight=weights[1],
            source_credibility_weight=weights[2],
            use_bm25=True,
            use_semantic_similarity=True,
            use_source_credibility=True,
        )
    )
    monkeypatch.setattr(ConfigLoader, "load_config", lambda self: cfg)
    ConfigLoader()._config = None

    monkeypatch.setattr(Search, "calculate_bm25_scores", staticmethod(lambda q, r: bm25_scores))
    monkeypatch.setattr(
        Search,
        "calculate_semantic_similarity",
        lambda self, q, r, query_embedding=None: semantic_scores,
    )
    monkeypatch.setattr(Search, "assess_source_credibility", lambda self, r: credibility_scores)


def test_rank_results_orders_by_weighted_scores(monkeypatch: pytest.MonkeyPatch) -> None:
    """Results are ordered by the weighted relevance score."""

    weights = [0.55, 0.3, 0.15]
    bm25_scores = [0.2, 0.5, 0.8]
    semantic_scores = [0.7, 0.3, 0.6]
    credibility_scores = [0.4, 0.9, 0.1]
    docs = [
        {"title": "alpha", "url": "https://example.com/a", "similarity": semantic_scores[0]},
        {"title": "beta", "url": "https://example.com/b", "similarity": semantic_scores[1]},
        {"title": "gamma", "url": "https://example.com/c", "similarity": semantic_scores[2]},
    ]

    configure_ranker(monkeypatch, weights, bm25_scores, semantic_scores, credibility_scores)

    ranked = Search.rank_results("q", copy.deepcopy(docs))

    bm25_norm = Search.normalize_scores(bm25_scores)
    credibility_norm = Search.normalize_scores(credibility_scores)
    duckdb_raw = [r["similarity"] for r in docs]
    semantic_norm, _ = Search.merge_semantic_scores(semantic_scores, duckdb_raw)
    final = combine_scores(bm25_norm, semantic_norm, credibility_norm, tuple(weights))
    expected_order = sorted(range(len(docs)), key=lambda i: final[i], reverse=True)
    ranked_titles = [r["title"] for r in ranked]
    assert ranked_titles == [docs[i]["title"] for i in expected_order]
    for r, score in zip(ranked, [final[i] for i in expected_order]):
        assert r["relevance_score"] == pytest.approx(score)


def test_rank_results_breaks_ties_deterministically(monkeypatch: pytest.MonkeyPatch) -> None:
    """Equal scores fall back to deterministic identifiers for ordering."""

    weights = [0.34, 0.33, 0.33]
    bm25_scores = [0.6, 0.6, 0.6]
    semantic_scores = [0.4, 0.4, 0.4]
    credibility_scores = [0.8, 0.8, 0.8]
    docs = [
        {
            "title": "alpha",
            "url": "https://example.com/a",
            "backend": "duckduckgo",
            "similarity": semantic_scores[0],
        },
        {
            "title": "beta",
            "url": "https://example.com/b",
            "backend": "serper",
            "similarity": semantic_scores[1],
        },
        {
            "title": "gamma",
            "url": "https://example.com/c",
            "backend": "duckduckgo",
            "similarity": semantic_scores[2],
        },
    ]

    configure_ranker(monkeypatch, weights, bm25_scores, semantic_scores, credibility_scores)

    expected_urls = [
        docs[index]["url"]
        for index, _ in sorted(
            enumerate(docs),
            key=lambda item: (
                docs[item[0]]["backend"],
                docs[item[0]]["url"],
                docs[item[0]]["title"],
                item[0],
            ),
        )
    ]

    ranked = Search.rank_results("q", copy.deepcopy(docs))
    assert [item["url"] for item in ranked] == expected_urls
    assert len({item["relevance_score"] for item in ranked}) == 1
    assert len({item["relevance_bucket"] for item in ranked}) == 1
    assert len({item["raw_relevance_bucket"] for item in ranked}) == 1
    for item in ranked:
        assert item["relevance_bucket"] == int(
            round(item["relevance_score"] * RANKING_BUCKET_SCALE)
        )
        assert item["raw_relevance_bucket"] == int(
            round(item["raw_merged_score"] * RANKING_BUCKET_SCALE)
        )

    reordered = list(reversed(docs))
    ranked_reordered = Search.rank_results("q", copy.deepcopy(reordered))
    assert [item["url"] for item in ranked_reordered] == expected_urls
    assert len({item["relevance_score"] for item in ranked_reordered}) == 1
    assert {item["relevance_bucket"] for item in ranked_reordered} == {
        ranked[0]["relevance_bucket"]
    }
    assert {item["raw_relevance_bucket"] for item in ranked_reordered} == {
        ranked[0]["raw_relevance_bucket"]
    }


@given(
    base=st.floats(min_value=0.0, max_value=1.0),
    delta=st.floats(
        min_value=-(0.49 / RANKING_BUCKET_SCALE),
        max_value=0.49 / RANKING_BUCKET_SCALE,
    ),
)
def test_rank_results_groups_nearby_scores(base: float, delta: float) -> None:
    """Scores inside one bucket reuse lexicographic tie-breaks deterministically."""

    weights = [0.5, 0.3, 0.2]
    bm25_scores = [0.7, 0.7, 0.7]
    semantic_scores = [0.4, 0.4, 0.4]
    credibility_scores = [0.6, 0.6, 0.6]
    docs = [
        {
            "title": "alpha",
            "url": "https://example.com/a",
            "backend": "duckduckgo",
            "similarity": 0.5,
        },
        {
            "title": "beta",
            "url": "https://example.com/b",
            "backend": "serper",
            "similarity": 0.5,
        },
        {
            "title": "gamma",
            "url": "https://example.com/c",
            "backend": "duckduckgo",
            "similarity": 0.5,
        },
    ]

    patcher = pytest.MonkeyPatch()
    try:
        configure_ranker(patcher, weights, bm25_scores, semantic_scores, credibility_scores)

        final_scores = [
            max(0.0, min(1.0, base)),
            max(0.0, min(1.0, base + delta)),
            max(0.0, min(1.0, base - delta)),
        ]
        buckets = {int(round(score * RANKING_BUCKET_SCALE)) for score in final_scores}
        assume(len(buckets) == 1)

        patcher.setattr(
            "autoresearch.search.core.combine_scores",
            lambda *_, **__: list(final_scores),
        )

        expected_urls = [
            docs[index]["url"]
            for index, _ in sorted(
                enumerate(docs),
                key=lambda item: (
                    docs[item[0]]["backend"],
                    docs[item[0]]["url"],
                    docs[item[0]]["title"],
                    item[0],
                ),
            )
        ]

        ranked = Search.rank_results("q", copy.deepcopy(docs))
        assert [item["url"] for item in ranked] == expected_urls
        assert {item["relevance_bucket"] for item in ranked} == buckets
        assert {item["raw_relevance_bucket"] for item in ranked} == {
            ranked[0]["raw_relevance_bucket"]
        }
    finally:
        patcher.undo()

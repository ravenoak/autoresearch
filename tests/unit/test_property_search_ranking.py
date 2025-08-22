from __future__ import annotations

import string
from typing import List

import pytest
from hypothesis import HealthCheck, given, settings, strategies as st

from autoresearch.config.loader import ConfigLoader
from autoresearch.config.models import ConfigModel, SearchConfig
from autoresearch.search import Search


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


@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    results=st.lists(
        st.tuples(
            st.text(alphabet=string.ascii_lowercase, min_size=1),
            st.floats(min_value=0, max_value=1),
            st.floats(min_value=0, max_value=1),
            st.floats(min_value=0, max_value=1),
        ),
        min_size=1,
        max_size=5,
    ),
    weights=st.lists(st.floats(min_value=0.01, max_value=1.0), min_size=3, max_size=3).map(
        lambda w: [x / sum(w) for x in w]
    ),
)
def test_rank_results_orders_by_weighted_scores(
    results: List[tuple[str, float, float, float]],
    weights: List[float],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Results are ordered by the weighted relevance score.

    References: docs/algorithms/bm25.md, docs/algorithms/semantic_similarity.md,
    docs/algorithms/source_credibility.md
    """
    titles = [t for t, _, _, _ in results]
    bm25_scores = [b for _, b, _, _ in results]
    semantic_scores = [s for _, _, s, _ in results]
    credibility_scores = [c for _, _, _, c in results]
    docs = [
        {"title": t, "url": f"https://example.com/{i}", "similarity": semantic_scores[i]}
        for i, t in enumerate(titles)
    ]

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

    ranked = Search.rank_results("q", docs)
    merged = [
        bm25_scores[i] * weights[0] + semantic_scores[i] * weights[1] for i in range(len(docs))
    ]
    final = [merged[i] + credibility_scores[i] * weights[2] for i in range(len(docs))]
    expected_order = sorted(range(len(docs)), key=lambda i: final[i], reverse=True)
    ranked_titles = [r["title"] for r in ranked]
    assert ranked_titles == [titles[i] for i in expected_order]
    for r, i in zip(ranked, expected_order):
        assert r["relevance_score"] == pytest.approx(final[i])

from unittest.mock import patch

import pytest

from autoresearch.config.models import ConfigModel, SearchConfig
from autoresearch.search import Search


def test_convex_combination_matches_docs(monkeypatch):
    search_cfg = SearchConfig.model_construct(
        semantic_similarity_weight=0.2,
        bm25_weight=0.6,
        source_credibility_weight=0.2,
    )
    cfg = ConfigModel.model_construct(search=search_cfg)
    cfg.api.role_permissions["anonymous"] = ["query"]
    monkeypatch.setattr("autoresearch.search.core.get_config", lambda: cfg)

    bm25 = [0.7, 0.2]
    semantic = [0.4, 0.9]
    cred = [0.5, 0.1]
    docs = [
        {"id": 0, "similarity": semantic[0]},
        {"id": 1, "similarity": semantic[1]},
    ]

    with (
        patch.object(
            Search, "calculate_bm25_scores", staticmethod(lambda q, results: bm25)
        ),
        patch.object(
            Search, "calculate_semantic_similarity", return_value=semantic
        ),
        patch.object(Search, "assess_source_credibility", return_value=cred),
    ):
        ranked = Search.rank_results("q", docs)

    w_s = search_cfg.semantic_similarity_weight
    w_b = search_cfg.bm25_weight
    w_c = search_cfg.source_credibility_weight
    expected = [w_b * bm25[i] + w_s * semantic[i] + w_c * cred[i] for i in range(2)]
    max_score = max(expected)
    normalized = [e / max_score for e in expected] if max_score > 0 else [0.0] * 2

    ranked_ids = [r["id"] for r in ranked]
    expected_ids = [i for i, _ in sorted(enumerate(normalized), key=lambda p: p[1], reverse=True)]
    assert ranked_ids == expected_ids

    for r in ranked:
        idx = r["id"]
        assert r["relevance_score"] == pytest.approx(normalized[idx])

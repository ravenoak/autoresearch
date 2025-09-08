from unittest.mock import patch

import numpy as np

from autoresearch.config.models import ConfigModel, SearchConfig
from autoresearch.search import Search


def test_cross_backend_ranking_consistent(monkeypatch):
    search_cfg = SearchConfig.model_construct(
        semantic_similarity_weight=0.5,
        bm25_weight=0.5,
        source_credibility_weight=0.0,
    )
    cfg = ConfigModel.model_construct(search=search_cfg)
    cfg.api.role_permissions["anonymous"] = ["query"]
    monkeypatch.setattr("autoresearch.search.core.get_config", lambda: cfg)

    backend_results = {
        "a": [{"id": "a", "title": "A", "snippet": ""}],
        "b": [{"id": "b", "title": "B", "snippet": ""}],
    }

    bm25_map = {"a": 0.2, "b": 0.9}
    sem_map = {"a": 0.8, "b": 0.3}

    def fake_bm25(query, docs):
        return [bm25_map[d["id"]] for d in docs]

    def fake_sem(self, query, docs, query_embedding=None):
        return [sem_map[d["id"]] for d in docs]

    with (
        patch.object(Search, "calculate_bm25_scores", staticmethod(fake_bm25)),
        patch.object(Search, "calculate_semantic_similarity", fake_sem),
        patch.object(
            Search,
            "assess_source_credibility",
            staticmethod(lambda docs: [0.0] * len(docs)),
        ),
    ):
        ranked1 = Search.cross_backend_rank("q", backend_results, np.zeros(1))
        ranked2 = Search.cross_backend_rank(
            "q", dict(reversed(list(backend_results.items()))), np.zeros(1)
        )

    expected = {k: 0.5 * (bm25_map[k] + sem_map[k]) for k in bm25_map}
    ordered = [k for k, _ in sorted(expected.items(), key=lambda p: p[1], reverse=True)]

    assert [r["id"] for r in ranked1] == ordered
    assert [r["id"] for r in ranked1] == [r["id"] for r in ranked2]

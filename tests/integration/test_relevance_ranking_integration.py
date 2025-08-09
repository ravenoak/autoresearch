import csv
from pathlib import Path
from unittest.mock import patch

import pytest
from autoresearch.search import Search
from autoresearch.config.models import ConfigModel, SearchConfig


def load_data():
    path = Path(__file__).resolve().parents[2] / "examples" / "search_evaluation.csv"
    data = {}
    with path.open() as f:
        reader = csv.DictReader(f)
        for row in reader:
            data.setdefault(row["query"], []).append(
                {
                    "bm25": float(row["bm25"]),
                    "semantic": float(row["semantic"]),
                    "credibility": float(row["credibility"]),
                    "relevance": int(row["relevance"]),
                }
            )
    return data


def test_example_weights_and_ranking(monkeypatch):
    data = load_data()

    search_cfg = SearchConfig.model_construct(
        semantic_similarity_weight=1.0,
        bm25_weight=0.0,
        source_credibility_weight=0.0,
    )
    cfg = ConfigModel(search=search_cfg)
    cfg.api.role_permissions["anonymous"] = ["query"]
    # Ensure weights sum to 1.0
    assert abs(
        cfg.search.semantic_similarity_weight
        + cfg.search.bm25_weight
        + cfg.search.source_credibility_weight
        - 1.0
    ) <= 0.001

    monkeypatch.setattr("autoresearch.search.core.get_config", lambda: cfg)

    for query, docs in data.items():
        with (
            patch.object(Search, "calculate_bm25_scores", return_value=[d["bm25"] for d in docs]),
            patch.object(Search, "calculate_semantic_similarity", return_value=[d["semantic"] for d in docs]),
            patch.object(Search, "assess_source_credibility", return_value=[d["credibility"] for d in docs]),
        ):
            ranked = Search.rank_results(query, [{"id": i} for i in range(len(docs))])
        expected_scores = [
            cfg.search.bm25_weight * d["bm25"]
            + cfg.search.semantic_similarity_weight * d["semantic"]
            + cfg.search.source_credibility_weight * d["credibility"]
            for d in docs
        ]
        max_score = max(expected_scores)
        top_indices = [
            i
            for i, s in enumerate(expected_scores)
            if abs(s - max_score) <= 1e-9
        ]
        assert ranked[0]["id"] in top_indices

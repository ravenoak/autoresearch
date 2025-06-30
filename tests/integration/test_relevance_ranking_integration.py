import csv
from pathlib import Path
from unittest.mock import patch

from autoresearch.search import Search
from autoresearch.config import ConfigModel, SearchConfig


def load_data():
    path = Path("examples/search_evaluation.csv")
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

    cfg = ConfigModel(
        search=SearchConfig(
            semantic_similarity_weight=0.85,
            bm25_weight=0.05,
            source_credibility_weight=0.1,
        )
    )
    cfg.api.role_permissions["anonymous"] = ["query"]
    # Ensure weights sum to 1.0
    assert abs(
        cfg.search.semantic_similarity_weight
        + cfg.search.bm25_weight
        + cfg.search.source_credibility_weight
        - 1.0
    ) <= 0.001

    monkeypatch.setattr("autoresearch.search.get_config", lambda: cfg)

    for query, docs in data.items():
        with (
            patch.object(Search, "calculate_bm25_scores", return_value=[d["bm25"] for d in docs]),
            patch.object(Search, "calculate_semantic_similarity", return_value=[d["semantic"] for d in docs]),
            patch.object(Search, "assess_source_credibility", return_value=[d["credibility"] for d in docs]),
        ):
            ranked = Search.rank_results(query, [{"id": i} for i in range(len(docs))])

        top_idx = ranked[0]["id"]
        assert docs[top_idx]["relevance"] == 1

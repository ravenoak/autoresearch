import csv
from pathlib import Path
from unittest.mock import patch

import pytest

from autoresearch.config.models import ConfigModel, SearchConfig
from autoresearch.search import Search


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
    assert (
        abs(
            cfg.search.semantic_similarity_weight
            + cfg.search.bm25_weight
            + cfg.search.source_credibility_weight
            - 1.0
        )
        <= 0.001
    ), "Search weights must sum to 1.0"

    monkeypatch.setattr("autoresearch.search.core.get_config", lambda: cfg)

    for query, docs in data.items():
        with (
            patch.object(
                Search, "calculate_bm25_scores", return_value=[d["bm25"] for d in docs]
            ),
            patch.object(
                Search,
                "calculate_semantic_similarity",
                return_value=[d["semantic"] for d in docs],
            ),
            patch.object(
                Search,
                "assess_source_credibility",
                return_value=[d["credibility"] for d in docs],
            ),
        ):
            ranked = Search.rank_results(query, [{"id": i} for i in range(len(docs))])

        # Compute expected score components for each document
        expected_components = []
        for d in docs:
            embedding_score = (d["semantic"] + 0.0) / 2
            merged_score = (
                cfg.search.bm25_weight * d["bm25"]
                + cfg.search.semantic_similarity_weight * embedding_score
            )
            final_score = (
                merged_score + cfg.search.source_credibility_weight * d["credibility"]
            )
            expected_components.append(
                {
                    "bm25_score": d["bm25"],
                    "semantic_score": d["semantic"],
                    "duckdb_score": 0.0,
                    "embedding_score": embedding_score,
                    "merged_score": merged_score,
                    "credibility_score": d["credibility"],
                    "relevance_score": final_score,
                }
            )

        expected_scores = [c["relevance_score"] for c in expected_components]

        # Verify ranking order
        expected_order = [
            idx
            for _, idx in sorted(
                zip(expected_scores, range(len(docs))),
                key=lambda pair: pair[0],
                reverse=True,
            )
        ]
        ranked_order = [r["id"] for r in ranked]
        assert ranked_order == expected_order, (
            f"Ranking mismatch for query '{query}': {ranked_order} != {expected_order}"
        )

        # Verify each result contains the full set of scores
        for result in ranked:
            expected = expected_components[result["id"]]
            for key, value in expected.items():
                assert key in result, f"Missing '{key}' in ranked result for '{query}'"
                assert result[key] == pytest.approx(value), (
                    f"{key} mismatch for doc {result['id']} in query '{query}'"
                )

        # Ensure the top result is one of the highest scoring documents
        max_score = max(expected_scores)
        top_indices = [
            i for i, s in enumerate(expected_scores) if abs(s - max_score) <= 1e-9
        ]
        assert ranked[0]["id"] in top_indices, (
            f"Top result id {ranked[0]['id']} not in expected top indices {top_indices}"
        )


def test_rank_results_empty_list():
    """Ranker should gracefully handle empty result lists."""
    ranked = Search.rank_results("query", [])
    assert ranked == [], "Expected empty list when no results are provided"

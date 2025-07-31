#!/usr/bin/env python
"""Evaluate relevance ranking using a labelled dataset."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Dict, List, Tuple
from unittest.mock import patch

from autoresearch.config.models import ConfigModel, SearchConfig
from autoresearch.config.loader import get_config
from autoresearch.search import Search


def load_data(path: Path) -> Dict[str, List[Dict[str, float]]]:
    """Load evaluation data grouped by query."""
    data: Dict[str, List[Dict[str, float]]] = {}
    with path.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            docs = data.setdefault(row["query"], [])
            docs.append(
                {
                    "bm25": float(row["bm25"]),
                    "semantic": float(row["semantic"]),
                    "credibility": float(row["credibility"]),
                    "relevance": float(row["relevance"]),
                }
            )
    return data


def evaluate(data: Dict[str, List[Dict[str, float]]], weights: Tuple[float, float, float]) -> Tuple[float, float]:
    """Return precision@1 and recall@1 for the provided weights."""
    sem_w, bm_w, cred_w = weights
    cfg = ConfigModel(search=SearchConfig(
        semantic_similarity_weight=sem_w,
        bm25_weight=bm_w,
        source_credibility_weight=cred_w,
    ))

    precisions: List[float] = []
    recalls: List[float] = []
    for query, docs in data.items():
        with (
            patch("autoresearch.search.get_config", return_value=cfg),
            patch.object(Search, "calculate_bm25_scores", return_value=[d["bm25"] for d in docs]),
            patch.object(Search, "calculate_semantic_similarity", return_value=[d["semantic"] for d in docs]),
            patch.object(Search, "assess_source_credibility", return_value=[d["credibility"] for d in docs]),
        ):
            ranked = Search.rank_results(query, [{"id": i} for i in range(len(docs))])

        order = [r["id"] for r in ranked]
        relevances = [d["relevance"] for d in docs]
        relevant_total = sum(relevances)
        top_rel = relevances[order[0]]
        precisions.append(top_rel)
        recalls.append(top_rel / relevant_total if relevant_total else 0.0)

    precision = sum(precisions) / len(precisions)
    recall = sum(recalls) / len(recalls)
    return precision, recall


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate ranking weights")
    parser.add_argument("dataset", type=Path, help="Path to evaluation CSV")
    parser.add_argument(
        "--weights",
        nargs=3,
        type=float,
        metavar=("SEM", "BM25", "CRED"),
        help="Override weights; by default use config values",
    )
    args = parser.parse_args()

    data = load_data(args.dataset)
    if args.weights:
        weights = (args.weights[0], args.weights[1], args.weights[2])
    else:
        cfg = get_config()
        weights = (
            cfg.search.semantic_similarity_weight,
            cfg.search.bm25_weight,
            cfg.search.source_credibility_weight,
        )

    precision, recall = evaluate(data, weights)
    print(f"Precision@1: {precision:.2f}  Recall@1: {recall:.2f}")


if __name__ == "__main__":
    main()

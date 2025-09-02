#!/usr/bin/env python
"""Compare ranking variants on synthetic corpora.

Usage:
    uv run scripts/ranking_sim.py --docs 50 --queries 10 --noise 0.2
"""
from __future__ import annotations

import argparse
import math
import random
from typing import Dict, List


def synthetic_corpus(queries: int, docs: int, noise: float) -> Dict[str, List[Dict[str, float]]]:
    """Generate synthetic relevance data."""
    data: Dict[str, List[Dict[str, float]]] = {}
    for q in range(queries):
        entries: List[Dict[str, float]] = []
        for _ in range(docs):
            rel = random.random()
            bm25 = max(0.0, min(1.0, rel + random.gauss(0.0, noise)))
            semantic = max(0.0, min(1.0, rel + random.gauss(0.0, noise)))
            cred = max(0.0, min(1.0, rel + random.gauss(0.0, noise)))
            entries.append(
                {"bm25": bm25, "semantic": semantic, "credibility": cred, "relevance": rel}
            )
        data[f"q{q}"] = entries
    return data


def _ndcg(relevances: List[float]) -> float:
    """Compute normalized discounted cumulative gain."""
    dcg = sum((2 ** r - 1) / math.log2(i + 2) for i, r in enumerate(relevances))
    ideal = sorted(relevances, reverse=True)
    idcg = sum((2 ** r - 1) / math.log2(i + 2) for i, r in enumerate(ideal))
    return dcg / idcg if idcg else 0.0


def _evaluate(
    weights: tuple[float, float, float],
    data: Dict[str, List[Dict[str, float]]],
) -> float:
    w_s, w_b, w_c = weights
    total = 0.0
    for docs in data.values():
        scores = [
            w_s * d["semantic"] + w_b * d["bm25"] + w_c * d["credibility"]
            for d in docs
        ]
        ranked = [
            docs[i]["relevance"]
            for i in sorted(
                range(len(docs)), key=lambda i: scores[i], reverse=True
            )
        ]
        total += _ndcg(ranked)
    return total / len(data)


def compare(data: Dict[str, List[Dict[str, float]]]) -> Dict[str, float]:
    """Evaluate standard ranking variants on data."""
    variants = {
        "bm25_only": (0.0, 1.0, 0.0),
        "semantic_only": (1.0, 0.0, 0.0),
        "credibility_only": (0.0, 0.0, 1.0),
        "combined": (0.3, 0.5, 0.2),
    }
    return {name: _evaluate(weights, data) for name, weights in variants.items()}


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Compare ranking variants on synthetic corpora",
    )
    parser.add_argument("--docs", type=int, default=50, help="documents per query")
    parser.add_argument("--queries", type=int, default=10, help="number of queries")
    parser.add_argument("--noise", type=float, default=0.1, help="noise standard deviation")
    args = parser.parse_args()
    if args.docs <= 0 or args.queries <= 0:
        parser.error("docs and queries must be positive")
    if args.noise < 0:
        parser.error("noise must be non-negative")
    data = synthetic_corpus(args.queries, args.docs, args.noise)
    scores = compare(data)
    for name, score in scores.items():
        print(f"{name}: {score:.3f}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python
"""Simulate convergence of relevance ranking.

Usage:
    uv run scripts/ranking_convergence.py --items 5
"""

from __future__ import annotations

import argparse
import random
from typing import Dict, List, Tuple


def rank_once(results: List[Dict[str, float]]) -> List[Dict[str, float]]:
    """Rank results by a fixed weighted score."""
    weights = {"bm25": 0.5, "semantic": 0.3, "cred": 0.2}
    for r in results:
        r["score"] = sum(r[k] * w for k, w in weights.items())
    return sorted(results, key=lambda r: r["score"], reverse=True)


def simulate(items: int) -> Tuple[int, List[int]]:
    """Return convergence step and final order for random scores."""
    results = [
        {
            "id": i,
            "bm25": random.random(),
            "semantic": random.random(),
            "cred": random.random(),
        }
        for i in range(items)
    ]
    previous = [r["id"] for r in results]
    ranked = rank_once(results)
    step = 1
    while True:
        order = [r["id"] for r in ranked]
        if order == previous:
            return step, order
        previous = order
        ranked = rank_once(ranked)
        step += 1


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Simulate ranking convergence",
    )
    parser.add_argument("--items", type=int, default=5, help="number of results")
    args = parser.parse_args()
    steps, order = simulate(args.items)
    print(f"final order: {order}")
    print(f"converged in {steps} step{'s' if steps != 1 else ''}")


if __name__ == "__main__":
    main()

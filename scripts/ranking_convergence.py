#!/usr/bin/env python
"""Simulate convergence of relevance ranking.

Usage:
    uv run scripts/ranking_convergence.py --items 5 --trials 100
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
    ranked = rank_once(results)
    step = 1
    order = [r["id"] for r in ranked]
    while True:
        reranked = rank_once(ranked)
        new_order = [r["id"] for r in reranked]
        if new_order == order:
            return step, order
        ranked = reranked
        order = new_order
        step += 1


def run_trials(trials: int, items: int) -> float:
    """Return the mean convergence step over ``trials`` random runs."""
    if trials <= 0:
        raise ValueError("trials must be positive")
    total = 0
    for _ in range(trials):
        step, _ = simulate(items)
        total += step
    return total / trials


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Simulate ranking convergence",
    )
    parser.add_argument("--items", type=int, default=5, help="number of results")
    parser.add_argument(
        "--trials",
        type=int,
        default=1,
        help="number of random simulations",
    )
    args = parser.parse_args()
    if args.items <= 0:
        raise SystemExit("--items must be positive")
    mean = run_trials(args.trials, args.items)
    print(f"mean convergence step: {mean}")


if __name__ == "__main__":
    main()

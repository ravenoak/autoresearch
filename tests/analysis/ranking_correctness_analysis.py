"""Simulate ranking by score to confirm descending ordering."""

from __future__ import annotations

import json
import random
from pathlib import Path


def rank_results(results: list[dict]) -> list[dict]:
    """Sort results by ``relevance_score`` descending."""
    return sorted(results, key=lambda r: r["relevance_score"], reverse=True)


def simulate(trials: int = 100, items: int = 5) -> dict[str, float]:
    """Generate random scores and verify the sorted order."""
    correct = 0
    for _ in range(trials):
        results = [
            {"title": str(i), "relevance_score": random.random()} for i in range(items)
        ]
        ranked = rank_results(results)
        scores = [r["relevance_score"] for r in ranked]
        if all(scores[i] >= scores[i + 1] for i in range(len(scores) - 1)):
            correct += 1
    ratio = correct / trials
    out_path = Path(__file__).with_name("ranking_correctness_metrics.json")
    out_path.write_text(json.dumps({"correctness": ratio}, indent=2) + "\n")
    return {"correctness": ratio}


def run() -> dict[str, float]:
    """Entry point for running the simulation."""
    return simulate()


if __name__ == "__main__":  # pragma: no cover
    print(json.dumps(run(), indent=2))

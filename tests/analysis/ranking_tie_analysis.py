"""Simulate ranking with duplicate scores to confirm stable sorting."""

from __future__ import annotations

import json
import random
from pathlib import Path


def rank_results(results: list[dict]) -> list[dict]:
    """Attach identical scores and sort descending, preserving input order."""
    for r in results:
        r["relevance_score"] = 1.0
    return sorted(results, key=lambda r: r["relevance_score"], reverse=True)


def simulate(trials: int = 100, items: int = 5) -> dict[str, float]:
    """Shuffle results and measure order preservation after ranking."""
    stable = 0
    for _ in range(trials):
        results = [
            {"title": str(i), "url": f"https://example.com/{i}"} for i in range(items)
        ]
        random.shuffle(results)
        ranked = rank_results(results)
        if [r["title"] for r in ranked] == [r["title"] for r in results]:
            stable += 1
    ratio = stable / trials
    out_path = Path(__file__).with_name("ranking_tie_metrics.json")
    out_path.write_text(json.dumps({"stability": ratio}, indent=2) + "\n")
    return {"stability": ratio}


def run() -> dict[str, float]:
    """Entry point for running the simulation."""
    return simulate()


if __name__ == "__main__":  # pragma: no cover
    print(json.dumps(run(), indent=2))

"""Benchmark ranking weight configurations on evaluation data.

Usage:
    uv run scripts/ranking_weight_benchmark.py --dataset examples/search_evaluation.csv
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import List, Tuple

import matplotlib.pyplot as plt

from autoresearch.search import Search


def evaluate_grid(
    data: dict[str, List[dict[str, float]]],
    cred_weight: float,
    step: float,
) -> Tuple[List[float], List[float]]:
    """Return semantic weights and corresponding NDCG scores.

    Args:
        data: Mapping of query to relevance metrics.
        cred_weight: Fixed weight for source credibility.
        step: Step size for semantic weight sweep.

    Returns:
        Tuple of semantic weights and average NDCG scores.
    """
    semantic_weights: List[float] = []
    scores: List[float] = []
    w = step
    while w <= 1.0 - cred_weight:
        bm25_weight = 1.0 - cred_weight - w
        score = Search.evaluate_weights((w, bm25_weight, cred_weight), data)
        semantic_weights.append(round(w, 3))
        scores.append(score)
        w = round(w + step, 10)
    return semantic_weights, scores


def plot_scores(weights: List[float], scores: List[float], output: Path) -> None:
    """Generate and save an NDCG plot."""
    plt.figure(figsize=(6, 4))
    plt.plot(weights, scores, marker="o")
    plt.xlabel("Semantic weight")
    plt.ylabel("NDCG")
    plt.title("Ranking quality vs semantic weight")
    plt.grid(True, linestyle=":", alpha=0.7)
    output.parent.mkdir(parents=True, exist_ok=True)
    plt.tight_layout()
    plt.savefig(output)
    plt.close()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Benchmark ranking weights and generate a performance plot",
    )
    examples_dir = Path(__file__).resolve().parents[1] / "examples"
    parser.add_argument(
        "--dataset",
        type=Path,
        default=examples_dir / "search_evaluation.csv",
        help="CSV file with bm25, semantic, credibility, and relevance columns",
    )
    parser.add_argument(
        "--cred-weight",
        type=float,
        default=0.2,
        help="Fixed weight for source credibility",
    )
    parser.add_argument(
        "--step",
        type=float,
        default=0.1,
        help="Step size for semantic weight sweep",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("docs/images/ranking_weight_ndcg.svg"),
        help="Where to save the generated plot",
    )
    args = parser.parse_args()

    if not args.dataset.is_file():
        parser.error(f"dataset not found: {args.dataset}")

    data = Search.load_evaluation_data(args.dataset)
    weights, scores = evaluate_grid(data, args.cred_weight, args.step)
    plot_scores(weights, scores, args.output)

    best_weight = weights[scores.index(max(scores))]
    bm25_weight = 1.0 - args.cred_weight - best_weight
    print(
        "best weights -> semantic="
        f"{best_weight:.2f}, bm25={bm25_weight:.2f}, cred={args.cred_weight:.2f}"
    )
    print(f"plot saved to {args.output}")


if __name__ == "__main__":
    main()

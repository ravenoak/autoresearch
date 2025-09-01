#!/usr/bin/env python
"""Compare ranking performance across synthetic datasets.

Usage:
    uv run scripts/ranking_dataset_comparison.py \
        --output docs/images/ranking_dataset_ndcg.svg
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Dict, List, Sequence
import random

import matplotlib.pyplot as plt

def _ndcg(relevances: List[float]) -> float:
    """Return NDCG for a ranked list of relevance scores."""

    dcg = relevances[0]
    for i, rel in enumerate(relevances[1:], start=2):
        dcg += rel / (i.bit_length())
    ideal = sorted(relevances, reverse=True)
    idcg = ideal[0]
    for i, rel in enumerate(ideal[1:], start=2):
        idcg += rel / (i.bit_length())
    return dcg / idcg if idcg else 0.0


def generate_dataset(noise: float, size: int = 5) -> Dict[str, List[Dict[str, float]]]:
    """Return synthetic evaluation data with adjustable noise."""

    data: Dict[str, List[Dict[str, float]]] = {}
    rng = random.Random(0)
    for q in range(3):
        docs: List[Dict[str, float]] = []
        for _ in range(size):
            bm25 = rng.random()
            semantic = rng.random()
            cred = rng.random()
            relevance = max(
                0.0,
                min(1.0, 0.6 * bm25 + 0.3 * semantic + 0.1 * cred + rng.gauss(0, noise)),
            )
            docs.append(
                {
                    "bm25": bm25,
                    "semantic": semantic,
                    "credibility": cred,
                    "relevance": relevance,
                }
            )
        data[f"q{q}"] = docs
    return data


def compare_datasets(
    noises: Sequence[float], weights: Sequence[float] = (0.5, 0.3, 0.2)
) -> Dict[str, float]:
    """Return NDCG scores for datasets generated with each noise level."""

    scores: Dict[str, float] = {}
    w_sem, w_bm, w_cred = weights
    for noise in noises:
        data = generate_dataset(noise)
        total = 0.0
        for docs in data.values():
            scores_vec = [
                w_sem * d["semantic"] + w_bm * d["bm25"] + w_cred * d["credibility"]
                for d in docs
            ]
            ranked = [
                docs[i]["relevance"]
                for i in sorted(range(len(docs)), key=lambda i: scores_vec[i], reverse=True)
            ]
            total += _ndcg(ranked)
        scores[f"noise-{noise}"] = total / len(data)
    return scores


def plot_scores(scores: Dict[str, float], output: Path) -> None:
    """Plot NDCG scores by dataset and save to ``output``."""

    labels = list(scores.keys())
    values = [scores[k] for k in labels]
    fig, ax = plt.subplots()
    ax.bar(labels, values, color="skyblue")
    ax.set_ylabel("NDCG")
    ax.set_xlabel("Dataset noise")
    ax.set_ylim(0, 1)
    for i, v in enumerate(values):
        ax.text(i, v + 0.01, f"{v:.2f}", ha="center")
    fig.tight_layout()
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output)
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Simulate ranking across synthetic datasets"
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("docs/images/ranking_dataset_ndcg.svg"),
        help="Where to save the plot",
    )
    args = parser.parse_args()

    scores = compare_datasets([0.0, 0.3])
    plot_scores(scores, args.output)
    print(f"plot saved to {args.output}")


if __name__ == "__main__":
    main()

"""Simulate weight tuning to confirm convergence."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import TypedDict

DATA: dict[str, list[dict[str, float]]] = {
    "q": [
        {"semantic": 0.9, "bm25": 0.7, "credibility": 0.8, "relevance": 3},
        {"semantic": 0.6, "bm25": 0.9, "credibility": 0.4, "relevance": 2},
        {"semantic": 0.3, "bm25": 0.2, "credibility": 0.6, "relevance": 1},
    ]
}


class WeightMetrics(TypedDict):
    """Metrics for a single grid search execution."""

    weights: tuple[float, float, float]
    ndcg: float


class ConvergenceStep(TypedDict):
    """Single measurement captured during convergence analysis."""

    step: float
    ndcg: float


class ConvergenceMetrics(TypedDict):
    """Metrics captured while halving the grid search step."""

    steps: list[ConvergenceStep]


def _write_metrics(path: Path, payload: WeightMetrics | ConvergenceMetrics) -> None:
    """Persist ``payload`` to ``path`` with canonical formatting."""

    path.write_text(json.dumps(payload, indent=2) + "\n")


def _ndcg(relevances: list[float]) -> float:
    dcg = sum((2**r - 1) / math.log2(i + 2) for i, r in enumerate(relevances))
    ideal = sorted(relevances, reverse=True)
    idcg = sum((2**r - 1) / math.log2(i + 2) for i, r in enumerate(ideal))
    return dcg / idcg if idcg else 0.0


def _evaluate(weights: tuple[float, float, float], data: dict[str, list[dict[str, float]]]) -> float:
    """Return mean NDCG for the given weights."""
    w_sem, w_bm, w_cred = weights
    total = 0.0
    for docs in data.values():
        scores = [
            w_sem * d["semantic"] + w_bm * d["bm25"] + w_cred * d["credibility"] for d in docs
        ]
        ranked = [
            docs[i]["relevance"]
            for i in sorted(range(len(docs)), key=lambda i: scores[i], reverse=True)
        ]
        total += _ndcg(ranked)
    return total / len(data)


def _grid_search(step: float) -> tuple[tuple[float, float, float], float]:
    """Return best weights and score for a grid of the given step."""
    best = (0.5, 0.3, 0.2)
    best_score = _evaluate(best, DATA)
    steps = [i * step for i in range(int(1 / step) + 1)]
    for w_sem in steps:
        for w_bm in steps:
            w_cred = 1.0 - w_sem - w_bm
            if 0 <= w_cred <= 1:
                score = _evaluate((w_sem, w_bm, w_cred), DATA)
                if score > best_score:
                    best, best_score = (w_sem, w_bm, w_cred), score
    return best, best_score


def run(step: float = 0.1) -> WeightMetrics:
    """Grid search weights and persist metrics to JSON."""
    best, best_score = _grid_search(step)
    result: WeightMetrics = {"weights": best, "ndcg": best_score}
    _write_metrics(Path(__file__).with_name("weight_tuning_metrics.json"), result)
    return result


def simulate_convergence(step: float = 0.1) -> ConvergenceMetrics:
    """Evaluate NDCG as the step size is halved to illustrate convergence."""
    current = step
    path: list[ConvergenceStep] = []
    for _ in range(3):
        _, score = _grid_search(current)
        path.append({"step": current, "ndcg": score})
        current /= 2
    result: ConvergenceMetrics = {"steps": path}
    _write_metrics(Path(__file__).with_name("weight_convergence_metrics.json"), result)
    return result


if __name__ == "__main__":  # pragma: no cover
    print(json.dumps(run(), indent=2))
    print(json.dumps(simulate_convergence(), indent=2))

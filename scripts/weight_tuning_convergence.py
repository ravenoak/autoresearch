#!/usr/bin/env python
"""Gradient-descent weight tuning demo.

Usage:
    uv run scripts/weight_tuning_convergence.py --iterations 100 --trials 5
"""

from __future__ import annotations

import argparse
import random
from statistics import mean, stdev
from typing import List, Tuple

TRAIN: List[Tuple[List[float], float]] = [
    ([0.9, 0.1, 0.8], 1.0),
    ([0.2, 0.8, 0.4], 0.7),
    ([0.5, 0.4, 0.6], 0.8),
    ([0.1, 0.2, 0.3], 0.3),
]


def step(weights: List[float], lr: float) -> Tuple[List[float], float]:
    grad = [0.0, 0.0, 0.0]
    loss = 0.0
    for feats, y in TRAIN:
        pred = sum(w * f for w, f in zip(weights, feats))
        err = pred - y
        loss += err * err
        for j, f in enumerate(feats):
            grad[j] += 2 * err * f
    new_weights = [w - lr * g for w, g in zip(weights, grad)]
    total = sum(new_weights) or 1.0
    new_weights = [max(0.0, w) / total for w in new_weights]
    return new_weights, loss / len(TRAIN)


def run_trial(iterations: int, lr: float) -> List[float]:
    weights = [random.random() for _ in range(3)]
    total = sum(weights)
    weights = [w / total for w in weights]
    for _ in range(iterations):
        weights, _ = step(weights, lr)
    return weights


def main() -> None:
    parser = argparse.ArgumentParser(description="Tune weights via gradient descent")
    parser.add_argument("--iterations", type=int, default=100, help="Training steps")
    parser.add_argument("--lr", type=float, default=0.1, help="Learning rate")
    parser.add_argument("--trials", type=int, default=5, help="Number of runs")
    args = parser.parse_args()

    finals = [run_trial(args.iterations, args.lr) for _ in range(args.trials)]
    avgs = [mean(w[i] for w in finals) for i in range(3)]
    stds = [stdev(w[i] for w in finals) if args.trials > 1 else 0.0 for i in range(3)]
    for i, (avg, sd) in enumerate(zip(avgs, stds)):
        print(f"weight_{i}: mean={avg:.3f} stdev={sd:.3f}")


if __name__ == "__main__":
    main()

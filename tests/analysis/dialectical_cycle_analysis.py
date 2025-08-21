"""Simulate dialectical coordination to estimate convergence error."""

from __future__ import annotations

import json
import random
import statistics
from pathlib import Path


def simulate(alpha: float = 0.5, loops: int = 6, trials: int = 100) -> dict[str, float]:
    """Run multiple trials of the coordination update."""
    finals = []
    g = 1.0
    for _ in range(trials):
        b_s = b_c = b_f = random.uniform(-1.0, 1.0)
        for _ in range(loops):
            new_b_s = (b_s + b_c + b_f) / 3
            epsilon = random.gauss(0.0, 0.1)
            new_b_c = b_s - epsilon
            new_b_f = b_s + alpha * (g - b_s)
            b_s, b_c, b_f = new_b_s, new_b_c, new_b_f
        finals.append(b_s)
    mean = statistics.fmean(finals)
    stdev = statistics.pstdev(finals)
    result = {"mean_final": mean, "stdev_final": stdev}
    out_path = Path(__file__).with_name("dialectical_metrics.json")
    out_path.write_text(json.dumps(result, indent=2) + "\n")
    return result


def run() -> dict[str, float]:
    """Entry point for running the simulation."""
    return simulate()


if __name__ == "__main__":  # pragma: no cover
    print(json.dumps(run(), indent=2))

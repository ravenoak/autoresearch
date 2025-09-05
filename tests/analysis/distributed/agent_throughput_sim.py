"""Estimate scheduler throughput across worker counts."""

from __future__ import annotations

import json
from pathlib import Path


def throughput_model(arrival_rate: float, service_rate: float, workers: int) -> float:
    """Return throughput using ``min(arrival_rate, workers * service_rate)"""
    if arrival_rate <= 0 or service_rate <= 0 or workers <= 0:
        raise ValueError("parameters must be positive")
    capacity = workers * service_rate
    return arrival_rate if arrival_rate < capacity else capacity


def run(arrival_rate: float = 5.0, service_rate: float = 2.0) -> dict[int, float]:
    """Compute throughput for varying worker counts and optionally plot results."""
    results: dict[int, float] = {}
    for workers in (1, 2, 4, 8):
        results[workers] = throughput_model(arrival_rate, service_rate, workers)
    out_dir = Path(__file__).resolve().parent
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        xs = sorted(results)
        ys = [results[w] for w in xs]
        plt.figure()
        plt.plot(xs, ys, marker="o")
        plt.xlabel("workers")
        plt.ylabel("tasks/sec")
        plt.title("Estimated throughput")
        plt.savefig(out_dir / "agent_throughput.svg", format="svg")
        plt.close()
    except Exception:  # pragma: no cover
        pass
    return results


if __name__ == "__main__":  # pragma: no cover
    print(json.dumps(run(), indent=2))

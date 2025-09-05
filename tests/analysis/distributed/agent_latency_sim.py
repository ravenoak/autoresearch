"""Estimate scheduler latency across worker counts."""

from __future__ import annotations

import json
from pathlib import Path


def latency_model(arrival_rate: float, service_rate: float, workers: int) -> float:
    """Approximate mean response time for an M/M/c queue."""
    if arrival_rate <= 0 or service_rate <= 0 or workers <= 0:
        raise ValueError("parameters must be positive")
    per_worker_arrival = arrival_rate / workers
    if per_worker_arrival >= service_rate:
        return float("inf")
    return 1.0 / (service_rate - per_worker_arrival)


def run(arrival_rate: float = 5.0, service_rate: float = 2.0) -> dict[int, float]:
    """Compute latency for varying worker counts and optionally plot results."""
    results: dict[int, float] = {}
    for workers in (1, 2, 4, 8):
        results[workers] = latency_model(arrival_rate, service_rate, workers)
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
        plt.ylabel("seconds")
        plt.title("Estimated latency")
        plt.savefig(out_dir / "agent_latency.svg", format="svg")
        plt.close()
    except Exception:  # pragma: no cover
        pass
    return results


if __name__ == "__main__":  # pragma: no cover
    print(json.dumps(run(), indent=2))

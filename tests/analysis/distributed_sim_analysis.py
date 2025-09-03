"""Analyze message throughput scaling for the distributed simulation."""

from __future__ import annotations

import json
from pathlib import Path

from scripts import distributed_sim


def run() -> dict[int, dict[str, float]]:
    """Run simulations for multiple worker counts and store metrics."""

    results: dict[int, dict[str, float]] = {}
    for workers in (1, 2, 4):
        metrics = distributed_sim.run_simulation(workers=workers, messages=100, loops=5)
        results[workers] = {
            "throughput": metrics["throughput"],
            "cpu_percent": metrics["cpu_percent"],
            "memory_mb": metrics["memory_mb"],
        }
    out_dir = Path(__file__).resolve().parent
    out_dir.joinpath("distributed_sim_metrics.json").write_text(json.dumps(results, indent=2))

    try:  # optional visualization
        import matplotlib.pyplot as plt

        xs = sorted(results)
        ys = [results[w]["throughput"] for w in xs]
        plt.figure()
        plt.plot(xs, ys, marker="o")
        plt.xlabel("workers")
        plt.ylabel("messages/sec")
        plt.title("Message throughput scaling")
        plt.savefig(out_dir / "distributed_sim_plot.png")
    except Exception:  # pragma: no cover
        pass
    return results


if __name__ == "__main__":  # pragma: no cover
    print(json.dumps(run(), indent=2))

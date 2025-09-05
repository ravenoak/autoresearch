"""Run distributed orchestrator benchmark and persist metrics."""

from __future__ import annotations

import json
from pathlib import Path

from scripts import distributed_orchestrator_perf_benchmark as bench


def run() -> dict[int, dict[str, float]]:
    """Execute benchmark for select worker counts and store metrics."""
    raw = bench.run_benchmark(max_workers=4, tasks=50, network_latency=0.005)
    results: dict[int, dict[str, float]] = {}
    for item in raw:
        workers = int(item["workers"])
        if workers in (1, 2, 4):
            results[workers] = {
                "avg_latency_s": item["avg_latency_s"],
                "throughput": item["throughput"],
                "memory_mb": item["memory_mb"],
            }
    out_dir = Path(__file__).resolve().parent
    out_dir.joinpath("distributed_orchestrator_perf_benchmark_metrics.json").write_text(
        json.dumps(results, indent=2) + "\n"
    )
    try:  # optional visualization
        import matplotlib.pyplot as plt

        xs = sorted(results)
        ys = [results[w]["throughput"] for w in xs]
        plt.figure()
        plt.plot(xs, ys, marker="o")
        plt.xlabel("workers")
        plt.ylabel("tasks/sec")
        plt.title("Orchestrator throughput scaling")
        plt.savefig(
            out_dir / "distributed_orchestrator_perf_benchmark_plot.png"
        )
    except Exception:  # pragma: no cover
        pass
    return results


if __name__ == "__main__":  # pragma: no cover
    print(json.dumps(run(), indent=2))

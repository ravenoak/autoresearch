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
    out_path = Path(__file__).with_name("distributed_orchestrator_perf_benchmark_metrics.json")
    out_path.write_text(json.dumps(results, indent=2) + "\n")
    return results


if __name__ == "__main__":  # pragma: no cover
    print(json.dumps(run(), indent=2))

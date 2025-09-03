"""Run task scheduling benchmark and persist metrics."""

from __future__ import annotations

import json
from pathlib import Path

from scripts import scheduling_resource_benchmark as bench


def run() -> dict[int, dict[str, float]]:
    """Execute benchmark for 1, 2, and 4 workers."""
    raw = bench.run_benchmark(
        max_workers=4,
        arrival_rate=3,
        service_rate=5,
        tasks=50,
        mem_per_task=5.0,
    )
    results: dict[int, dict[str, float]] = {}
    for item in raw:
        workers = int(item["workers"])
        if workers in (1, 2, 4):
            results[workers] = {
                "utilization": item["utilization"],
                "avg_queue_length": item["avg_queue_length"],
                "throughput": item["throughput"],
                "mem_kb": item["mem_kb"],
                "expected_memory": item["expected_memory"],
            }
    out_path = Path(__file__).with_name("scheduling_resource_metrics.json")
    out_path.write_text(json.dumps(results, indent=2) + "\n")
    return results


if __name__ == "__main__":  # pragma: no cover
    print(json.dumps(run(), indent=2))

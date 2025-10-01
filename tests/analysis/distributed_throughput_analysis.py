"""Measure throughput scaling for the process-based scheduler."""

from __future__ import annotations

import json
from pathlib import Path

from scripts import simulate_distributed_coordination as sim_dc


def run() -> dict[int, dict[str, float]]:
    """Run simulations for multiple worker counts and persist metrics."""
    results: dict[int, dict[str, float]] = {}
    for workers in (1, 2, 4):
        samples = [
            sim_dc.run_simulation(workers=workers, tasks=50, loops=5)
            for _ in range(3)
        ]
        results[workers] = {
            "throughput": sum(sample["throughput"] for sample in samples) / len(samples),
            "cpu_percent": sum(sample["cpu_percent"] for sample in samples) / len(samples),
            "memory_mb": sum(sample["memory_mb"] for sample in samples) / len(samples),
        }
    out_path = Path(__file__).with_name("distributed_throughput_metrics.json")
    out_path.write_text(json.dumps(results, indent=2))
    return results


if __name__ == "__main__":  # pragma: no cover
    print(json.dumps(run(), indent=2))

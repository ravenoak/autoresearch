"""Measure throughput scaling for the process-based scheduler."""

from __future__ import annotations

import json
from pathlib import Path

from scripts import simulate_distributed_coordination as sim_dc


def run() -> dict[int, dict[str, float]]:
    """Run simulations for multiple worker counts and persist metrics."""
    results: dict[int, dict[str, float]] = {}
    for workers in (1, 2, 4):
        metrics = sim_dc.run_simulation(workers=workers, tasks=50, loops=5)
        results[workers] = {
            "throughput": metrics["throughput"],
            "cpu_percent": metrics["cpu_percent"],
            "memory_mb": metrics["memory_mb"],
        }
    out_path = Path(__file__).with_name("distributed_throughput_metrics.json")
    out_path.write_text(json.dumps(results, indent=2))
    return results


if __name__ == "__main__":  # pragma: no cover
    print(json.dumps(run(), indent=2))

#!/usr/bin/env python3
"""Benchmark recovery overhead in a distributed orchestrator.

Usage:
    uv run scripts/distributed_recovery_benchmark.py --workers 2 --tasks 100 \
        --fail-rate 0.1
"""

from __future__ import annotations

import argparse
import json

from scripts.orchestrator_distributed_sim import run_simulation


def main(workers: int, tasks: int, fail_rate: float) -> dict[str, float]:
    """Execute benchmark and print summary metrics."""

    metrics = run_simulation(workers=workers, tasks=tasks, fail_rate=fail_rate)
    print(
        json.dumps(
            {
                "throughput": metrics["throughput"],
                "recovery_ratio": metrics["recovery_ratio"],
                "cpu_percent": metrics["cpu_percent"],
                "memory_mb": metrics["memory_mb"],
            }
        )
    )
    return metrics


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Distributed recovery benchmark")
    parser.add_argument("--workers", type=int, default=2, help="worker processes")
    parser.add_argument("--tasks", type=int, default=100, help="tasks to execute")
    parser.add_argument("--fail-rate", type=float, default=0.1, help="failure probability per task")
    args = parser.parse_args()
    main(args.workers, args.tasks, args.fail_rate)

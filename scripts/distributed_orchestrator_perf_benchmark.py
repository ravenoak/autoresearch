#!/usr/bin/env python3
"""Benchmark distributed orchestrator latency, throughput, and memory.

Usage:
    uv run scripts/distributed_orchestrator_perf_benchmark.py --max-workers 4 \
        --tasks 100 --network-latency 0.005 --task-time 0.01
"""
from __future__ import annotations

import argparse
import json
from typing import Dict, List

import distributed_orchestrator_sim


def run_benchmark(
    max_workers: int,
    tasks: int,
    network_latency: float = 0.005,
    task_time: float = 0.005,
) -> List[Dict[str, float]]:
    """Run simulations across worker counts and gather performance metrics.

    Args:
        max_workers: Highest worker count to evaluate.
        tasks: Number of tasks per simulation run.
        network_latency: Simulated dispatch latency per task in seconds.
        task_time: Simulated processing time per task in seconds.

    Returns:
        List of metrics dictionaries, one per worker count.
    """
    if max_workers <= 0 or tasks <= 0 or network_latency < 0 or task_time <= 0:
        raise ValueError(
            "max_workers and tasks must be positive; latency must be >= 0 and"
            " task_time must be > 0"
        )

    results: List[Dict[str, float]] = []
    for workers in range(1, max_workers + 1):
        metrics = distributed_orchestrator_sim.run_simulation(
            workers=workers,
            tasks=tasks,
            network_latency=network_latency,
            task_time=task_time,
        )
        results.append(
            {
                "workers": float(workers),
                "avg_latency_s": metrics["avg_latency_s"],
                "throughput": metrics["throughput"],
                "memory_mb": metrics["memory_mb"],
            }
        )
    return results


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Distributed orchestrator performance benchmark"
    )
    parser.add_argument("--max-workers", type=int, required=True, help="Max workers to test")
    parser.add_argument("--tasks", type=int, required=True, help="Tasks per simulation run")
    parser.add_argument(
        "--network-latency",
        type=float,
        default=0.005,
        help="Simulated dispatch latency per task in seconds",
    )
    parser.add_argument(
        "--task-time",
        type=float,
        default=0.005,
        help="Simulated processing time per task in seconds",
    )
    args = parser.parse_args()

    results = run_benchmark(
        args.max_workers,
        args.tasks,
        args.network_latency,
        args.task_time,
    )
    print(json.dumps(results))


if __name__ == "__main__":  # pragma: no cover
    main()

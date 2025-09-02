#!/usr/bin/env python3
"""Demonstrate distributed scheduling throughput using multiple processes.

Usage:
    uv run python scripts/simulate_distributed_coordination.py --workers 2
"""

from __future__ import annotations

import argparse
import time
import json
from concurrent.futures import ProcessPoolExecutor

from autoresearch.resource_monitor import ResourceMonitor


def _square(x: int) -> int:
    """Return the square of ``x``."""

    return x * x


def run_simulation(workers: int, tasks: int, loops: int = 10) -> dict[str, float]:
    """Run tasks across processes and collect performance metrics.

    Args:
        workers: Number of worker processes.
        tasks: How many integers to square per loop.
        loops: How many scheduling loops to execute.

    Returns:
        Dictionary with throughput, CPU percentage, memory usage, and total
        tasks processed.
    """

    if workers <= 0 or tasks <= 0 or loops <= 0:
        raise SystemExit("workers, tasks, and loops must be positive")

    # Use a lightweight monitor so metrics reflect process-level usage.
    monitor = ResourceMonitor(interval=0.05)
    monitor.start()
    start = time.perf_counter()
    with ProcessPoolExecutor(max_workers=workers) as executor:
        for _ in range(loops):
            list(executor.map(_square, range(tasks)))
    duration = time.perf_counter() - start
    monitor.stop()

    total_tasks = tasks * loops
    throughput = total_tasks / duration if duration > 0 else float("inf")
    cpu = float(monitor.cpu_gauge._value.get())
    mem = float(monitor.mem_gauge._value.get())
    return {
        "tasks": float(total_tasks),
        "duration_s": duration,
        "throughput": throughput,
        "cpu_percent": cpu,
        "memory_mb": mem,
    }


def main(workers: int, tasks: int, loops: int = 10) -> dict[str, float]:
    """Run the simulation and print summary metrics."""

    metrics = run_simulation(workers=workers, tasks=tasks, loops=loops)
    print(
        f"Processed {int(metrics['tasks'])} tasks in {metrics['duration_s']:.3f}s "
        f"with {workers} workers"
    )
    print(
        json.dumps(
            {
                "throughput": metrics["throughput"],
                "cpu_percent": metrics["cpu_percent"],
                "memory_mb": metrics["memory_mb"],
            }
        )
    )
    return metrics


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Distributed coordination demo")
    parser.add_argument("--workers", type=int, default=2, help="number of workers")
    parser.add_argument("--tasks", type=int, default=100, help="tasks per loop")
    parser.add_argument("--loops", type=int, default=10, help="scheduling loops")
    args = parser.parse_args()
    main(args.workers, args.tasks, args.loops)

#!/usr/bin/env python3
"""Generate synthetic scheduling load with optional network delay.

Usage:
    uv run scripts/distributed_orchestrator_sim.py --workers 2 --tasks 100 \
        --network-latency 0.005 --task-time 0.01

Each task waits ``network_latency`` seconds to mimic dispatch over a network
before a worker process sleeps for ``task_time`` seconds to emulate work. The
run reports average latency, throughput, and resource consumption.
"""

from __future__ import annotations

import argparse
import json
import time
from concurrent.futures import ProcessPoolExecutor
from itertools import repeat

from autoresearch.resource_monitor import ResourceMonitor


def _handle_task(network_latency: float, task_time: float) -> int:
    """Sleep to emulate network delay and processing."""

    time.sleep(network_latency)
    time.sleep(task_time)
    return 0


def run_simulation(
    workers: int,
    tasks: int,
    network_latency: float = 0.005,
    task_time: float = 0.005,
) -> dict[str, float]:
    """Process tasks across workers and collect performance metrics.

    Args:
        workers: Number of worker processes.
        tasks: Total tasks to dispatch.
        network_latency: Simulated dispatch latency per task in seconds.
        task_time: Simulated processing time per task in seconds.

    Returns:
        Dictionary with average latency, throughput, CPU percentage, and memory
        usage in megabytes.
    """

    if workers <= 0 or tasks <= 0 or network_latency < 0 or task_time <= 0:
        raise SystemExit("workers, tasks, latency, and task_time must be > 0")

    monitor = ResourceMonitor(interval=0.05)
    monitor.start()
    start = time.perf_counter()
    with ProcessPoolExecutor(max_workers=workers) as executor:
        list(
            executor.map(
                _handle_task,
                repeat(network_latency, tasks),
                repeat(task_time, tasks),
            )
        )
    duration = time.perf_counter() - start
    monitor.stop()

    throughput = tasks / duration if duration > 0 else float("inf")
    avg_latency = duration / tasks
    cpu = float(monitor.cpu_gauge._value.get())
    mem = float(monitor.mem_gauge._value.get())
    return {
        "avg_latency_s": avg_latency,
        "throughput": throughput,
        "cpu_percent": cpu,
        "memory_mb": mem,
    }


def main(workers: int, tasks: int, network_latency: float, task_time: float) -> dict[str, float]:
    """Run the simulation and print summary metrics."""

    metrics = run_simulation(
        workers=workers, tasks=tasks, network_latency=network_latency, task_time=task_time
    )
    print(
        json.dumps(
            {
                "avg_latency_s": metrics["avg_latency_s"],
                "throughput": metrics["throughput"],
                "cpu_percent": metrics["cpu_percent"],
                "memory_mb": metrics["memory_mb"],
            }
        )
    )
    return metrics


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Distributed orchestrator scheduling simulation"
    )
    parser.add_argument("--workers", type=int, default=2, help="number of worker processes")
    parser.add_argument("--tasks", type=int, default=100, help="tasks to schedule")
    parser.add_argument(
        "--network-latency",
        type=float,
        default=0.005,
        help="simulated dispatch latency per task (s)",
    )
    parser.add_argument(
        "--task-time",
        type=float,
        default=0.005,
        help="simulated compute time per task (s)",
    )
    args = parser.parse_args()
    main(args.workers, args.tasks, args.network_latency, args.task_time)


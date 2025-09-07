#!/usr/bin/env python3
"""Simulate distributed orchestrator with failure recovery.

Usage:
    uv run scripts/orchestrator_distributed_sim.py --workers 2 --tasks 100 \
        --network-latency 0.005 --task-time 0.01 --fail-rate 0.1
"""

from __future__ import annotations

import argparse
import json
import random
import time
from concurrent.futures import ProcessPoolExecutor
from itertools import repeat

from autoresearch.resource_monitor import ResourceMonitor


def _handle_task(network_latency: float, task_time: float, fail_rate: float) -> int:
    """Execute a task and simulate a single retry on failure.

    Returns 1 when a recovery path executes, 0 otherwise.
    """

    time.sleep(network_latency)
    if random.random() < fail_rate:
        # Retry once after another dispatch delay and service time.
        time.sleep(network_latency)
        time.sleep(task_time)
        return 1
    time.sleep(task_time)
    return 0


def run_simulation(
    workers: int,
    tasks: int,
    network_latency: float = 0.005,
    task_time: float = 0.005,
    fail_rate: float = 0.0,
) -> dict[str, float]:
    """Process tasks across workers, collecting performance and recovery metrics.

    Args:
        workers: Number of worker processes.
        tasks: Total tasks to dispatch.
        network_latency: Simulated dispatch latency per task in seconds.
        task_time: Simulated processing time per task in seconds.
        fail_rate: Probability a task fails once and requires recovery.

    Returns:
        Dictionary with average latency, throughput, CPU percentage, memory usage,
        and recovery ratio.
    """

    if (
        workers <= 0
        or tasks <= 0
        or network_latency < 0
        or task_time <= 0
        or not 0.0 <= fail_rate < 1.0
    ):
        raise SystemExit(
            "workers, tasks, latency, and task_time must be > 0;"
            " fail_rate must satisfy 0 <= fail_rate < 1"
        )

    monitor = ResourceMonitor(interval=0.05)
    monitor.start()
    start = time.perf_counter()
    with ProcessPoolExecutor(max_workers=workers) as executor:
        recoveries = sum(
            executor.map(
                _handle_task,
                repeat(network_latency, tasks),
                repeat(task_time, tasks),
                repeat(fail_rate, tasks),
            )
        )
    duration = time.perf_counter() - start
    monitor.stop()

    throughput = tasks / duration if duration > 0 else float("inf")
    avg_latency = duration / tasks
    cpu = float(monitor.cpu_gauge._value.get())
    mem = float(monitor.mem_gauge._value.get())
    recovery_ratio = recoveries / tasks
    return {
        "avg_latency_s": avg_latency,
        "throughput": throughput,
        "cpu_percent": cpu,
        "memory_mb": mem,
        "recovery_ratio": recovery_ratio,
    }


def main(
    workers: int,
    tasks: int,
    network_latency: float,
    task_time: float,
    fail_rate: float,
) -> dict[str, float]:
    """Run the simulation and print summary metrics."""

    metrics = run_simulation(
        workers=workers,
        tasks=tasks,
        network_latency=network_latency,
        task_time=task_time,
        fail_rate=fail_rate,
    )
    print(json.dumps(metrics))
    return metrics


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Distributed orchestrator simulation with recovery"
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
        "--task-time", type=float, default=0.005, help="simulated compute time per task (s)"
    )
    parser.add_argument(
        "--fail-rate",
        type=float,
        default=0.0,
        help="probability a task fails and triggers recovery",
    )
    args = parser.parse_args()
    main(args.workers, args.tasks, args.network_latency, args.task_time, args.fail_rate)

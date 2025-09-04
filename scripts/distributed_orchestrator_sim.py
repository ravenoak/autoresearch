#!/usr/bin/env python3
"""Simulate scheduling latency and resource consumption for a distributed
orchestrator.

Usage:
    uv run scripts/distributed_orchestrator_sim.py --workers 2 --tasks 100 \\
        --network-latency 0.005 --task-time 0.01

The simulation dispatches tasks to worker processes and records average
end-to-end latency alongside CPU and memory usage. Each task incurs a
configurable dispatch delay (``network_latency``) and execution time
(``task_time``) to model network and compute costs separately.
"""

from __future__ import annotations

import argparse
import json
import time
from concurrent.futures import ProcessPoolExecutor
from statistics import mean

from autoresearch import resource_monitor as rm
from autoresearch.resource_monitor import ResourceMonitor


def _task(duration: float) -> float:
    """Sleep for ``duration`` seconds and return completion time."""

    time.sleep(duration)
    return time.perf_counter()


def run_simulation(
    workers: int,
    tasks: int,
    network_latency: float = 0.005,
    task_time: float = 0.005,
) -> dict[str, float]:
    """Dispatch tasks and measure scheduling latency and resource usage.

    Args:
        workers: Number of worker processes.
        tasks: Total tasks to schedule.
        network_latency: Simulated dispatch latency per task in seconds.
        task_time: Simulated compute time per task in seconds.

    Returns:
        Dictionary with average latency, throughput, CPU percentage, and memory
        usage in megabytes.
    """

    if workers <= 0 or tasks <= 0 or network_latency < 0 or task_time < 0:
        raise SystemExit("workers and tasks must be positive; latency and task_time must be >= 0")

    original_gpu = rm._get_gpu_stats
    rm._get_gpu_stats = lambda: (0.0, 0.0)
    monitor = ResourceMonitor(interval=0.05)
    monitor.start()
    start = time.perf_counter()
    try:
        with ProcessPoolExecutor(max_workers=workers) as executor:
            starts: list[float] = []
            futures = []
            for _ in range(tasks):
                dispatch_start = time.perf_counter()
                # Model network latency before submitting the task to the worker.
                time.sleep(network_latency)
                starts.append(dispatch_start)
                futures.append(executor.submit(_task, task_time))
            completions = [f.result() for f in futures]
    finally:
        duration = time.perf_counter() - start
        monitor.stop()
        rm._get_gpu_stats = original_gpu

    latencies = [c - s for s, c in zip(starts, completions)]
    avg_latency = mean(latencies) if latencies else 0.0
    throughput = tasks / duration if duration > 0 else float("inf")
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
    parser = argparse.ArgumentParser(description="Distributed orchestrator scheduling simulation")
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

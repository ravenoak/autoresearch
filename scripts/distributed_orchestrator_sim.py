#!/usr/bin/env python3
"""Simulate distributed scheduling latency using an M/M/c queue model.

Usage:
    uv run scripts/distributed_orchestrator_sim.py --workers 2 --tasks 100 \\
        --network-latency 0.005 --task-time 0.01

The simulation applies queueing theory to estimate average latency and
throughput for a distributed orchestrator. Each task experiences a network
dispatch delay (``network_latency``) before reaching one of ``workers``
identical servers that process tasks in ``task_time`` seconds. The model
assumes Poisson arrivals and exponential service times as described in
``docs/orchestrator_perf.md``.
"""

from __future__ import annotations

import argparse
import json
import math


def run_simulation(
    workers: int,
    tasks: int,
    network_latency: float = 0.005,
    task_time: float = 0.005,
) -> dict[str, float]:
    """Return queue-based latency and throughput estimates.

    Args:
        workers: Number of worker processes.
        tasks: Total tasks to schedule (unused but kept for parity with benchmarks).
        network_latency: Network dispatch delay per task in seconds.
        task_time: Service time per task in seconds.

    Returns:
        Dictionary with average latency, throughput, and placeholder CPU and
        memory metrics (always ``0``).
    """

    if workers <= 0 or tasks <= 0 or network_latency <= 0 or task_time <= 0:
        raise SystemExit("workers, tasks, latency, and task_time must be > 0")

    arrival_rate = 1.0 / network_latency
    service_rate = 1.0 / task_time
    rho = arrival_rate / (workers * service_rate)
    if rho >= 1:
        raise SystemExit("system is unstable; arrival rate must be < workers * service_rate")

    ratio = arrival_rate / service_rate
    sum_terms = sum((ratio**n) / math.factorial(n) for n in range(workers))
    last = (ratio**workers) / (math.factorial(workers) * (1 - rho))
    p0 = 1 / (sum_terms + last)
    lq = (p0 * (ratio**workers) * rho) / (math.factorial(workers) * (1 - rho) ** 2)
    wq = lq / arrival_rate
    avg_latency = network_latency + wq + task_time
    throughput = arrival_rate
    return {
        "avg_latency_s": avg_latency,
        "throughput": throughput,
        "cpu_percent": 0.0,
        "memory_mb": 0.0,
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

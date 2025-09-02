#!/usr/bin/env python3
"""Simulate orchestrator queue metrics.

Usage:
    uv run scripts/orchestrator_perf_sim.py --workers 2 --arrival-rate 3 \
        --service-rate 5 --tasks 50 --mem-per-task 0.5
"""
from __future__ import annotations

import argparse
import json
import math
from typing import Dict


def queue_metrics(workers: int, arrival_rate: float, service_rate: float) -> Dict[str, float]:
    """Return utilization and average queue length for an M/M/c queue."""
    if workers <= 0:
        raise ValueError("workers must be positive")
    if arrival_rate <= 0 or service_rate <= 0:
        raise ValueError("rates must be positive")

    rho = arrival_rate / (workers * service_rate)
    if rho >= 1:
        raise ValueError("system is unstable; utilization >= 1")

    ratio = arrival_rate / service_rate
    sum_terms = sum((ratio**n) / math.factorial(n) for n in range(workers))
    last = (ratio**workers) / (math.factorial(workers) * (1 - rho))
    p0 = 1 / (sum_terms + last)
    lq = (p0 * (ratio**workers) * rho) / (math.factorial(workers) * (1 - rho) ** 2)
    return {"utilization": rho, "avg_queue_length": lq}


def simulate(
    workers: int,
    arrival_rate: float,
    service_rate: float,
    tasks: int,
    mem_per_task: float,
) -> Dict[str, float]:
    """Combine queue metrics with a simple memory model."""
    metrics = queue_metrics(workers, arrival_rate, service_rate)
    metrics["expected_memory"] = tasks * mem_per_task
    return metrics


def main() -> None:
    parser = argparse.ArgumentParser(description="Queue and resource simulation")
    parser.add_argument("--workers", type=int, required=True, help="Number of workers")
    parser.add_argument(
        "--arrival-rate",
        type=float,
        required=True,
        help="Task arrival rate (tasks/s)",
    )
    parser.add_argument(
        "--service-rate",
        type=float,
        required=True,
        help="Per-worker service rate (tasks/s)",
    )
    parser.add_argument("--tasks", type=int, required=True, help="Number of tasks")
    parser.add_argument(
        "--mem-per-task",
        type=float,
        default=1.0,
        help="Memory per task in MB",
    )
    args = parser.parse_args()
    metrics = simulate(
        args.workers, args.arrival_rate, args.service_rate, args.tasks, args.mem_per_task
    )
    print(json.dumps(metrics))


if __name__ == "__main__":  # pragma: no cover
    main()

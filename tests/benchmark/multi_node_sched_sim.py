"""Simulate multi-node scheduling with failure recovery."""

from __future__ import annotations

import argparse
import heapq
import json
import random
from typing import TypedDict


class ScheduleMetrics(TypedDict):
    """Structured metrics captured from the simulation."""

    throughput: float
    overhead: float
    duration_s: float
    executions: float


def run_simulation(
    *,
    workers: int,
    tasks: int,
    network_latency: float = 0.01,
    task_time: float = 0.01,
    fail_rate: float = 0.1,
) -> ScheduleMetrics:
    """Run a scheduling simulation and return throughput and overhead metrics.

    Args:
        workers: Number of concurrent workers.
        tasks: Total tasks to execute.
        network_latency: Dispatch latency per attempt in seconds.
        task_time: Service time per attempt in seconds.
        fail_rate: Probability that an attempt fails and must be retried.

    Returns:
        Dictionary with throughput, overhead, total duration, and executions.
    """
    if workers < 1 or tasks < 1 or not 0 <= fail_rate < 1:
        raise SystemExit("invalid parameters")

    rng = random.Random(0)
    available = [0.0] * workers
    heapq.heapify(available)
    total_attempts = 0

    for _ in range(tasks):
        done = False
        while not done:
            start = heapq.heappop(available)
            duration = network_latency + task_time
            finish = start + duration
            total_attempts += 1
            if rng.random() < fail_rate:
                heapq.heappush(available, finish)
            else:
                heapq.heappush(available, finish)
                done = True

    total_time = max(available)
    throughput = tasks / total_time if total_time > 0 else float("inf")
    overhead = total_attempts / tasks
    return ScheduleMetrics(
        throughput=throughput,
        overhead=overhead,
        duration_s=total_time,
        executions=float(total_attempts),
    )


def main() -> None:
    """CLI wrapper for the simulation."""
    parser = argparse.ArgumentParser(
        description="Multi-node scheduling simulation with failures"
    )
    parser.add_argument("--workers", type=int, default=2, help="concurrent workers")
    parser.add_argument("--tasks", type=int, default=100, help="tasks to run")
    parser.add_argument(
        "--network-latency",
        type=float,
        default=0.01,
        help="network latency per attempt in seconds",
    )
    parser.add_argument("--task-time", type=float, default=0.01, help="service time per attempt")
    parser.add_argument(
        "--fail-rate",
        type=float,
        default=0.1,
        help="failure probability per attempt",
    )
    args = parser.parse_args()
    metrics = run_simulation(
        workers=args.workers,
        tasks=args.tasks,
        network_latency=args.network_latency,
        task_time=args.task_time,
        fail_rate=args.fail_rate,
    )
    print(json.dumps(metrics))


if __name__ == "__main__":
    main()

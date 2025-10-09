#!/usr/bin/env python3
"""Benchmark scheduler scaling and resource usage.

The benchmark simulates I/O-bound tasks that sleep for roughly 8 ms and ensures
each worker processes at least 150 ms of work per measurement batch. With those
defaults and a deterministic warm-up batch, doubling the number of workers
consistently delivers about 1.8–2.0x throughput. The heavier per-task workload
makes the scaling trend visible even after amortising coordination overhead, so
multi-worker runs retain a clear advantage over the single-worker baseline. The
script now surfaces per-sample means and standard deviations to highlight the
reduced variance after warm-up.

Usage:
    uv run scripts/scheduling_resource_benchmark.py --max-workers 4 --tasks 100 \
        --arrival-rate 3 --service-rate 5 --mem-per-task 0.5
"""
from __future__ import annotations

import argparse
import json
from typing import Dict, List

from autoresearch.orchestrator_perf import (
    DEFAULT_MIN_MEASURE_DURATION,
    DEFAULT_SLEEP_DURATION,
    benchmark_scheduler,
    simulate,
)


def run_benchmark(
    max_workers: int,
    arrival_rate: float,
    service_rate: float,
    tasks: int,
    mem_per_task: float,
    sleep_duration: float = DEFAULT_SLEEP_DURATION,
    min_measure_duration: float = DEFAULT_MIN_MEASURE_DURATION,
) -> List[Dict[str, float]]:
    """Run simulation and micro-benchmark across worker counts.

    Args:
        max_workers: Highest worker count to evaluate.
        arrival_rate: Task arrival rate (tasks/s).
        service_rate: Per-worker service rate (tasks/s).
        tasks: Number of tasks to process.
        mem_per_task: Memory per task in megabytes.
        sleep_duration: Time each task simulates work by sleeping (seconds).
        min_measure_duration: Minimum per-worker runtime targeted for each
            throughput sample (seconds).

    Returns:
        List of metrics for each worker count, including per-sample throughput
        statistics from ``benchmark_scheduler``.
    """
    if max_workers <= 0:
        raise ValueError("max_workers must be positive")

    results: List[Dict[str, float]] = []
    for workers in range(1, max_workers + 1):
        metrics = simulate(workers, arrival_rate, service_rate, tasks, mem_per_task)
        bench = benchmark_scheduler(
            workers,
            tasks,
            mem_per_task,
            sleep_duration=sleep_duration,
            min_measure_duration=min_measure_duration,
        )
        metrics.update(vars(bench))
        metrics["workers"] = workers
        results.append(metrics)
    return results


def main() -> None:
    parser = argparse.ArgumentParser(description="Scheduler scaling benchmark")
    parser.add_argument("--max-workers", type=int, required=True, help="Max workers to test")
    parser.add_argument(
        "--arrival-rate", type=float, required=True, help="Task arrival rate (tasks/s)"
    )
    parser.add_argument(
        "--service-rate", type=float, required=True, help="Per-worker service rate (tasks/s)"
    )
    parser.add_argument("--tasks", type=int, required=True, help="Number of tasks to simulate")
    parser.add_argument("--mem-per-task", type=float, default=1.0, help="Memory per task in MB")
    parser.add_argument(
        "--sleep-duration",
        type=float,
        default=DEFAULT_SLEEP_DURATION,
        help="Per-task sleep used to simulate work (seconds)",
    )
    parser.add_argument(
        "--min-measure-duration",
        type=float,
        default=DEFAULT_MIN_MEASURE_DURATION,
        help="Minimum per-worker runtime targeted for each measurement (seconds)",
    )
    args = parser.parse_args()

    results = run_benchmark(
        args.max_workers,
        args.arrival_rate,
        args.service_rate,
        args.tasks,
        args.mem_per_task,
        args.sleep_duration,
        args.min_measure_duration,
    )
    print(json.dumps(results))


if __name__ == "__main__":  # pragma: no cover
    main()

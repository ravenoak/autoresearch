#!/usr/bin/env python3
"""Simulate orchestrator queue metrics and run a scheduling benchmark.

Usage:
    uv run scripts/orchestrator_perf_sim.py --workers 2 --arrival-rate 3 \
        --service-rate 5 --tasks 50 --mem-per-task 0.5 --benchmark
"""
from __future__ import annotations

import argparse
import json
from typing import Dict

from autoresearch.orchestrator_perf import benchmark_scheduler, simulate


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
    parser.add_argument(
        "--benchmark",
        action="store_true",
        help="Run micro-benchmark for scheduling throughput",
    )
    args = parser.parse_args()

    metrics: Dict[str, float] = simulate(
        args.workers, args.arrival_rate, args.service_rate, args.tasks, args.mem_per_task
    )
    if args.benchmark:
        benchmark_result = benchmark_scheduler(args.workers, args.tasks)
        # Convert BenchmarkResult to dict for JSON serialization
        benchmark_metrics = {
            "benchmark_throughput": benchmark_result.throughput,
            "benchmark_cpu_time": benchmark_result.cpu_time,
            "benchmark_mem_kb": benchmark_result.mem_kb,
            "benchmark_throughput_mean": benchmark_result.throughput_mean,
            "benchmark_throughput_stddev": benchmark_result.throughput_stddev,
        }
        metrics.update(benchmark_metrics)
    print(json.dumps(metrics))


if __name__ == "__main__":  # pragma: no cover
    main()

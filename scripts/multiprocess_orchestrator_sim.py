#!/usr/bin/env python3
"""Simulate multi-process orchestrator throughput and latency.

Usage:
    uv run scripts/multiprocess_orchestrator_sim.py --workers 2 --tasks 100 \
        --network-latency 0.005 --task-time 0.005

The simulation dispatches tasks to worker processes. Each task waits
``network_latency`` seconds to emulate network delay then sleeps for
``task_time`` seconds to mimic processing. The script reports observed
and theoretical metrics derived from the M/M/c model in
``docs/algorithms/distributed_perf.md``.
"""
from __future__ import annotations

import argparse
import json
import time
from concurrent.futures import ProcessPoolExecutor
from itertools import repeat
from math import factorial


def _work(network_latency: float, task_time: float) -> None:
    """Sleep to emulate network delay and processing."""

    time.sleep(network_latency)
    time.sleep(task_time)


def _theoretical_metrics(
    workers: int, network_latency: float, task_time: float
) -> tuple[float, float]:
    """Return expected latency and throughput for stable systems."""

    lam = 1 / network_latency
    mu = 1 / task_time
    rho = lam / (workers * mu)
    if rho >= 1:
        raise ValueError("system is unstable; choose higher workers or lower rates")
    p0_inv = sum((lam / mu) ** n / factorial(n) for n in range(workers))
    p0_inv += (lam / mu) ** workers / (factorial(workers) * (1 - rho))
    p0 = 1 / p0_inv
    lq = ((lam / mu) ** workers * rho / (factorial(workers) * (1 - rho) ** 2)) * p0
    wq = lq / lam
    latency = network_latency + wq + task_time
    throughput = lam
    return latency, throughput


def run_simulation(
    workers: int, tasks: int, network_latency: float, task_time: float
) -> dict[str, float]:
    """Execute tasks across worker processes and gather metrics."""

    if workers <= 0 or tasks <= 0 or network_latency <= 0 or task_time <= 0:
        raise SystemExit("workers, tasks, network_latency, and task_time must be > 0")
    theory_latency, theory_throughput = _theoretical_metrics(
        workers, network_latency, task_time
    )
    start = time.perf_counter()
    with ProcessPoolExecutor(max_workers=workers) as executor:
        list(
            executor.map(
                _work, repeat(network_latency, tasks), repeat(task_time, tasks)
            )
        )
    duration = time.perf_counter() - start
    observed_throughput = tasks / duration if duration > 0 else float("inf")
    observed_latency = duration / tasks
    return {
        "avg_latency_s": observed_latency,
        "throughput": observed_throughput,
        "theoretical_latency_s": theory_latency,
        "theoretical_throughput": theory_throughput,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Multi-process orchestration throughput and latency simulation"
    )
    parser.add_argument("--workers", type=int, default=2, help="number of worker processes")
    parser.add_argument("--tasks", type=int, default=100, help="tasks to schedule")
    parser.add_argument(
        "--network-latency",
        type=float,
        default=0.005,
        help="simulated network delay per task (s)",
    )
    parser.add_argument(
        "--task-time",
        type=float,
        default=0.005,
        help="simulated processing time per task (s)",
    )
    args = parser.parse_args()
    metrics = run_simulation(args.workers, args.tasks, args.network_latency, args.task_time)
    print(json.dumps(metrics))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Simulate distributed orchestrator throughput and latency via queueing theory.

Usage:
    uv run scripts/distributed_perf_sim.py --max-workers 4 --arrival-rate 100 \
        --service-rate 120 --network-delay 0.005
"""
from __future__ import annotations

import argparse
import json
from typing import Dict, List

from autoresearch.orchestrator_perf import queue_metrics


def simulate(
    max_workers: int,
    arrival_rate: float,
    service_rate: float,
    network_delay: float = 0.0,
) -> List[Dict[str, float]]:
    """Return queueing metrics across worker counts.

    Args:
        max_workers: Highest number of workers to evaluate.
        arrival_rate: Task arrival rate (tasks/s).
        service_rate: Per-worker service rate (tasks/s).
        network_delay: Network delay before tasks reach workers (s).

    Returns:
        A list of metrics dictionaries for each worker count.
    """
    if max_workers <= 0:
        raise SystemExit("max_workers must be positive")
    if arrival_rate <= 0 or service_rate <= 0:
        raise SystemExit("rates must be positive")
    if network_delay < 0:
        raise SystemExit("network_delay cannot be negative")

    results: List[Dict[str, float]] = []
    for workers in range(1, max_workers + 1):
        metrics = queue_metrics(workers, arrival_rate, service_rate)
        wait_q = metrics["avg_queue_length"] / arrival_rate
        latency = network_delay + wait_q + 1 / service_rate
        results.append(
            {
                "workers": float(workers),
                "throughput": arrival_rate,
                "latency_s": latency,
                "avg_queue_length": metrics["avg_queue_length"],
            }
        )
    return results


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Analytical distributed orchestrator performance simulation"
    )
    parser.add_argument("--max-workers", type=int, required=True, help="max workers to model")
    parser.add_argument("--arrival-rate", type=float, required=True, help="task arrival rate")
    parser.add_argument("--service-rate", type=float, required=True, help="per-worker service rate")
    parser.add_argument(
        "--network-delay", type=float, default=0.0, help="network delay per task in seconds"
    )
    args = parser.parse_args()

    results = simulate(args.max_workers, args.arrival_rate, args.service_rate, args.network_delay)
    print(json.dumps(results))


if __name__ == "__main__":  # pragma: no cover
    main()

#!/usr/bin/env python3
"""Compare queueing predictions with simulated latency and throughput.

Usage:
    uv run scripts/distributed_perf_compare.py --max-workers 3 \
        --arrival-rate 80 --service-rate 100 --tasks 1000 \
        --network-delay 0.005 --seed 1 \
        --output docs/data/distributed_perf_summary.json
"""
from __future__ import annotations

import argparse
import json
import random
from pathlib import Path
from typing import Dict, List

from autoresearch.orchestrator_perf import queue_metrics


def _simulate_mmc(
    tasks: int,
    workers: int,
    arrival_rate: float,
    service_rate: float,
    network_delay: float,
    rng: random.Random,
) -> Dict[str, float]:
    """Return measured throughput and latency via discrete-event simulation.

    The simulation models an M/M/c queue where tasks arrive according to an
    exponential distribution and each worker draws service times from another
    exponential distribution. Network delay is added to each task's latency.

    Args:
        tasks: Total tasks to simulate.
        workers: Number of worker servers.
        arrival_rate: Mean task arrival rate (tasks/s).
        service_rate: Mean service rate per worker (tasks/s).
        network_delay: Delay before service in seconds.
        rng: Random number generator for reproducibility.

    Returns:
        Dictionary with measured throughput and latency in seconds.
    """
    if tasks <= 0:
        raise SystemExit("tasks must be positive")
    if workers <= 0:
        raise SystemExit("workers must be positive")
    if arrival_rate <= 0 or service_rate <= 0:
        raise SystemExit("rates must be positive")
    if network_delay < 0:
        raise SystemExit("network_delay cannot be negative")

    arrival = 0.0
    first_arrival = None
    last_completion = 0.0
    total_latency = 0.0
    worker_available = [0.0] * workers
    for _ in range(tasks):
        arrival += rng.expovariate(arrival_rate)
        if first_arrival is None:
            first_arrival = arrival
        idx = min(range(workers), key=lambda i: worker_available[i])
        start = max(arrival, worker_available[idx])
        service_time = rng.expovariate(service_rate)
        completion = start + service_time
        worker_available[idx] = completion
        total_latency += completion - arrival + network_delay
        last_completion = max(last_completion, completion)
    assert first_arrival is not None
    duration = last_completion - first_arrival
    throughput = tasks / duration if duration > 0 else float("inf")
    avg_latency = total_latency / tasks
    return {"throughput": throughput, "latency_s": avg_latency}


def compare(
    max_workers: int,
    arrival_rate: float,
    service_rate: float,
    tasks: int,
    network_delay: float = 0.0,
    seed: int | None = None,
) -> List[Dict[str, Dict[str, float]]]:
    """Compare theoretical and simulated metrics across worker counts.

    Args:
        max_workers: Highest number of workers to evaluate.
        arrival_rate: Task arrival rate (tasks/s).
        service_rate: Service rate per worker (tasks/s).
        tasks: Number of tasks to simulate.
        network_delay: Network delay per task in seconds.
        seed: Seed for the pseudo-random generator.

    Returns:
        List of dictionaries keyed by ``workers`` with ``predicted`` and
        ``measured`` metrics for throughput and latency.
    """
    if max_workers <= 0:
        raise SystemExit("max_workers must be positive")
    rng = random.Random(seed)
    results: List[Dict[str, Dict[str, float]]] = []
    for workers in range(1, max_workers + 1):
        predicted_q = queue_metrics(workers, arrival_rate, service_rate)
        wait_q = predicted_q["avg_queue_length"] / arrival_rate
        pred_latency = network_delay + wait_q + 1 / service_rate
        pred_throughput = min(arrival_rate, workers * service_rate)
        measured = _simulate_mmc(tasks, workers, arrival_rate, service_rate, network_delay, rng)
        results.append(
            {
                "workers": float(workers),
                "predicted": {
                    "throughput": pred_throughput,
                    "latency_s": pred_latency,
                },
                "measured": measured,
            }
        )
    return results


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Compare queueing predictions with simulated measurements"
    )
    parser.add_argument("--max-workers", type=int, required=True, help="max workers to model")
    parser.add_argument("--arrival-rate", type=float, required=True, help="task arrival rate")
    parser.add_argument("--service-rate", type=float, required=True, help="per-worker service rate")
    parser.add_argument("--tasks", type=int, default=1000, help="tasks to simulate")
    parser.add_argument(
        "--network-delay", type=float, default=0.0, help="network delay per task in seconds"
    )
    parser.add_argument("--seed", type=int, default=0, help="random seed for reproducibility")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("docs/data/distributed_perf_summary.json"),
        help="Where to write the summary JSON",
    )
    args = parser.parse_args()

    results = compare(
        args.max_workers,
        args.arrival_rate,
        args.service_rate,
        args.tasks,
        args.network_delay,
        args.seed,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(results, indent=2))
    print(json.dumps(results))


if __name__ == "__main__":  # pragma: no cover
    main()

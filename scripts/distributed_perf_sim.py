#!/usr/bin/env python3
"""Simulate distributed orchestrator throughput and latency via queueing theory.

Usage:
    uv run scripts/distributed_perf_sim.py --max-workers 4 --arrival-rate 100 \
        --service-rate 120 --network-delay 0.005 \
        --output docs/images/distributed_perf.svg
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, List, Sequence

import matplotlib.pyplot as plt

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
        throughput = min(arrival_rate, workers * service_rate)
        if arrival_rate < workers * service_rate:
            metrics = queue_metrics(workers, arrival_rate, service_rate)
            wait_q = metrics["avg_queue_length"] / arrival_rate
            latency = network_delay + wait_q + 1 / service_rate
            queue_len = metrics["avg_queue_length"]
        else:
            latency = float("inf")
            queue_len = float("inf")
        results.append(
            {
                "workers": float(workers),
                "throughput": throughput,
                "latency_s": latency,
                "avg_queue_length": queue_len,
            }
        )
    return results


def _plot(results: Sequence[Dict[str, float]], output: Path) -> None:
    """Save throughput and latency curves to ``output``.

    Args:
        results: Metrics returned from :func:`simulate`.
        output: Destination path for the SVG plot.
    """
    workers = [r["workers"] for r in results]
    throughput = [r["throughput"] for r in results]
    latency = [r["latency_s"] for r in results]

    fig, ax1 = plt.subplots()
    ax1.plot(workers, throughput, marker="o", color="tab:blue")
    ax1.set_xlabel("Workers")
    ax1.set_ylabel("Throughput (tasks/s)", color="tab:blue")
    ax1.tick_params(axis="y", labelcolor="tab:blue")

    ax2 = ax1.twinx()
    ax2.plot(workers, latency, marker="o", color="tab:red")
    ax2.set_ylabel("Latency (s)", color="tab:red")
    ax2.tick_params(axis="y", labelcolor="tab:red")

    fig.tight_layout()
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output)
    plt.close(fig)


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
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("docs/images/distributed_perf.svg"),
        help="Where to save the throughput/latency plot",
    )
    args = parser.parse_args()

    results = simulate(
        args.max_workers, args.arrival_rate, args.service_rate, args.network_delay
    )
    _plot(results, args.output)
    print(json.dumps(results))


if __name__ == "__main__":  # pragma: no cover
    main()

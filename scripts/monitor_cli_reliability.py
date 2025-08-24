#!/usr/bin/env python3
"""Simulate monitor CLI latency and failure rates.

Usage:
    uv run scripts/monitor_cli_reliability.py --runs 1000 --fail-rate 0.05

Runs a Monte Carlo model of metrics collection. Each simulated run may fail
with a configured probability and records a latency sample. Results include
average latency and success rate.
"""

from __future__ import annotations

import argparse
import random
import statistics
import sys


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Simulate monitor CLI reliability and latency.")
    parser.add_argument(
        "--runs",
        type=int,
        default=1000,
        help="number of simulated runs",
    )
    parser.add_argument(
        "--fail-rate",
        type=float,
        default=0.02,
        help="probability a run fails to collect metrics",
    )
    return parser.parse_args()


def simulate(runs: int, fail_rate: float) -> tuple[float, float]:
    failures = 0
    latencies: list[float] = []
    for _ in range(runs):
        if random.random() < fail_rate:
            failures += 1
            continue
        latencies.append(random.gauss(100, 15))
    success_rate = 1 - failures / runs
    avg_latency = statistics.mean(latencies) if latencies else float("nan")
    return avg_latency, success_rate


def main() -> None:
    args = parse_args()
    if args.runs <= 0 or not (0.0 <= args.fail_rate <= 1.0):
        print(
            "runs must be positive and fail-rate between 0 and 1",
            file=sys.stderr,
        )
        sys.exit(1)
    avg_latency, success_rate = simulate(args.runs, args.fail_rate)
    print(f"average_latency_ms={avg_latency:.1f}")
    print(f"success_rate={success_rate:.3f}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Simulate webhook retries and timeouts.

Usage:
    uv run scripts/streaming_webhook_sim.py --success-prob 0.8 --retries 3

This utility models independent webhook delivery attempts with a fixed timeout
per attempt. It reports the empirical success rate and average number of
attempts over the given trials.
"""

from __future__ import annotations

import argparse
import random
from dataclasses import dataclass


@dataclass
class SimulationResult:
    """Store results from ``simulate_webhook``."""

    success_rate: float
    avg_attempts: float


def simulate_webhook(
    success_prob: float,
    retries: int,
    timeout: float,
    trials: int = 1000,
    seed: int | None = None,
) -> SimulationResult:
    """Run a Monte Carlo simulation of webhook retry behavior."""

    if not 0 <= success_prob <= 1:
        raise ValueError("success_prob must be between 0 and 1")
    if retries < 0:
        raise ValueError("retries must be non-negative")
    rng = random.Random(seed)
    successes = 0
    total_attempts = 0
    for _ in range(trials):
        for attempt in range(retries + 1):
            total_attempts += 1
            if rng.random() < success_prob:
                successes += 1
                break
    success_rate = successes / trials
    avg_attempts = total_attempts / trials
    return SimulationResult(success_rate, avg_attempts)


def main() -> None:
    parser = argparse.ArgumentParser(description="Simulate webhook retry behavior and timeouts.")
    parser.add_argument(
        "--success-prob",
        type=float,
        default=0.7,
        help="Probability a single attempt succeeds within timeout.",
    )
    parser.add_argument(
        "--retries",
        type=int,
        default=3,
        help="Maximum number of retries after the initial attempt.",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=1.0,
        help="Timeout per attempt in seconds.",
    )
    parser.add_argument("--trials", type=int, default=1000, help="Number of simulated requests.")
    args = parser.parse_args()
    result = simulate_webhook(args.success_prob, args.retries, args.timeout, args.trials)
    total_time = result.avg_attempts * args.timeout
    print(f"success rate: {result.success_rate:.3f}")
    print(f"avg attempts: {result.avg_attempts:.2f}")
    print(f"expected time: {total_time:.2f}s")


if __name__ == "__main__":
    main()

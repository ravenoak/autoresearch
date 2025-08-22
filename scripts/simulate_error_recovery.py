#!/usr/bin/env python
"""Estimate retries needed for exponential backoff.

Usage:
    uv run scripts/simulate_error_recovery.py --p 0.3 --trials 1000
"""

from __future__ import annotations

import argparse
import random

from autoresearch.error_recovery import retry_with_backoff


def trial(p: float) -> int:
    attempts = 0

    def action() -> bool:
        nonlocal attempts
        attempts += 1
        return random.random() < p

    try:
        retry_with_backoff(action, max_retries=100)
    except RuntimeError:
        pass
    return attempts


def main() -> None:
    parser = argparse.ArgumentParser(description="Simulate error recovery retries")
    parser.add_argument("--p", type=float, default=0.3, help="success probability")
    parser.add_argument("--trials", type=int, default=1000)
    args = parser.parse_args()
    total = sum(trial(args.p) for _ in range(args.trials))
    print(f"average attempts: {total / args.trials:.2f}")


if __name__ == "__main__":
    main()

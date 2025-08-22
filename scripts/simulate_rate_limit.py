#!/usr/bin/env python
"""Simulate token bucket API rate limiting under load.

Usage:
    uv run scripts/simulate_rate_limit.py --requests 20 --rate 5 --burst 10

The ``--requests`` flag sets the total requests. ``--rate`` is the refill
rate in tokens per second. ``--burst`` defines the bucket capacity.
"""

from __future__ import annotations

import argparse
import time


def simulate(reqs: int, rate: float, burst: int) -> None:
    """Print whether each request is allowed or throttled."""
    tokens = float(burst)
    last = time.monotonic()
    allowed = 0
    for i in range(reqs):
        now = time.monotonic()
        tokens = min(burst, tokens + (now - last) * rate)
        last = now
        if tokens >= 1:
            tokens -= 1
            allowed += 1
            status = "allowed"
        else:
            status = "throttled"
        print(f"request {i + 1:03d}: {status}")
    print(f"{allowed}/{reqs} requests allowed")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Simulate API rate limiting with a token bucket",
    )
    parser.add_argument(
        "--requests",
        type=int,
        default=20,
        help="total number of requests to send",
    )
    parser.add_argument(
        "--rate",
        type=float,
        default=5.0,
        help="refill rate in tokens per second",
    )
    parser.add_argument(
        "--burst",
        type=int,
        default=10,
        help="bucket capacity",
    )
    args = parser.parse_args()
    if args.requests <= 0 or args.rate <= 0 or args.burst <= 0:
        parser.error("all arguments must be positive")
    simulate(args.requests, args.rate, args.burst)


if __name__ == "__main__":
    main()

#!/usr/bin/env python
"""Simulate token bucket API rate limiting under load.

Usage examples::

    # bursty traffic: 5 quick requests repeated over 20 total
    uv run scripts/simulate_rate_limit.py burst --requests 20 --rate 5 --burst 10 --group 5

    # distributed clocks with up to 0.4 s of drift
    uv run scripts/simulate_rate_limit.py drift --requests 20 --rate 5 --burst 10 --drift 0.4

The ``--requests`` flag sets the total requests. ``--rate`` is the refill
rate in tokens per second. ``--burst`` defines the bucket capacity. The
``burst`` scenario groups requests into bursts separated by sleeps to
exercise refilling. The ``drift`` scenario adds random clock drift to
each request to mimic distributed nodes.
"""

from __future__ import annotations

import argparse
import random
import time


def _update_tokens(tokens: float, last: float, now: float, rate: float, burst: int) -> float:
    """Return the new token count after refilling."""
    tokens = min(float(burst), tokens + max(0.0, now - last) * rate)
    return tokens


def _consume(tokens: float) -> tuple[float, str]:
    if tokens >= 1:
        return tokens - 1, "allowed"
    return tokens, "throttled"


def simulate_uniform(reqs: int, rate: float, burst: int) -> None:
    """Print whether each uniformly timed request is allowed."""
    tokens = float(burst)
    last = time.monotonic()
    allowed = 0
    for i in range(reqs):
        now = time.monotonic()
        tokens = _update_tokens(tokens, last, now, rate, burst)
        last = now
        tokens, status = _consume(tokens)
        if status == "allowed":
            allowed += 1
        print(f"request {i + 1:03d}: {status}")
    print(f"{allowed}/{reqs} requests allowed")


def simulate_burst(reqs: int, rate: float, burst: int, group: int) -> None:
    """Send requests in groups to stress the refill logic."""
    tokens = float(burst)
    last = time.monotonic()
    allowed = 0
    for i in range(reqs):
        now = time.monotonic()
        tokens = _update_tokens(tokens, last, now, rate, burst)
        last = now
        tokens, status = _consume(tokens)
        if status == "allowed":
            allowed += 1
        print(f"request {i + 1:03d}: {status}")
        if (i + 1) % group == 0 and i + 1 < reqs:
            # sleep long enough to allow replenishment
            time.sleep(group / rate)
    print(f"{allowed}/{reqs} requests allowed")


def simulate_drift(reqs: int, rate: float, burst: int, drift: float) -> None:
    """Apply random clock drift each iteration to mimic distributed nodes."""
    tokens = float(burst)
    last = time.monotonic()
    allowed = 0
    for i in range(reqs):
        now = time.monotonic() + random.uniform(-drift, drift)
        tokens = _update_tokens(tokens, last, now, rate, burst)
        last = now
        tokens, status = _consume(tokens)
        if status == "allowed":
            allowed += 1
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
    sub = parser.add_subparsers(dest="scenario", required=True)

    burst_p = sub.add_parser("burst", help="group requests into bursts")
    burst_p.add_argument(
        "--group",
        type=int,
        default=5,
        help="number of requests per burst",
    )

    drift_p = sub.add_parser("drift", help="add random clock drift")
    drift_p.add_argument(
        "--drift",
        type=float,
        default=0.5,
        help="maximum clock skew in seconds",
    )

    uniform_p = sub.add_parser("uniform", help="uniform request spacing")

    args = parser.parse_args()
    if args.requests <= 0 or args.rate <= 0 or args.burst <= 0:
        parser.error("all arguments must be positive")

    if args.scenario == "burst":
        if args.group <= 0:
            parser.error("--group must be positive")
        simulate_burst(args.requests, args.rate, args.burst, args.group)
    elif args.scenario == "drift":
        if args.drift < 0:
            parser.error("--drift must be non-negative")
        simulate_drift(args.requests, args.rate, args.burst, args.drift)
    else:
        simulate_uniform(args.requests, args.rate, args.burst)


if __name__ == "__main__":
    main()

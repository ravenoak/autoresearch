#!/usr/bin/env python3
"""Simulate API auth errors with configurable credential distributions.

Usage:
    uv run scripts/simulate_api_auth_errors.py --requests 1000 \
        --missing 0.2 --invalid 0.3 --rate-limit 0.1 --seed 0
"""

from __future__ import annotations

import argparse
import random
from collections import Counter


def simulate(
    requests: int,
    missing_prob: float,
    invalid_prob: float,
    rate_limit_prob: float,
    seed: int | None = None,
) -> dict[int, int]:
    """Return frequency of status codes for simulated requests."""
    if min(missing_prob, invalid_prob, rate_limit_prob) < 0:
        raise ValueError("probabilities must be non-negative")
    total = missing_prob + invalid_prob + rate_limit_prob
    if total > 1:
        raise ValueError("probabilities sum to more than 1")
    rng = random.Random(seed)
    counts: Counter[int] = Counter()
    for _ in range(requests):
        r = rng.random()
        if r < missing_prob:
            counts[400] += 1
        elif r < missing_prob + invalid_prob:
            counts[401] += 1
        elif r < total:
            counts[429] += 1
        else:
            counts[200] += 1
    return dict(counts)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Simulate API auth error responses",
    )
    parser.add_argument(
        "--requests",
        type=int,
        default=1000,
        help="number of simulated requests",
    )
    parser.add_argument(
        "--missing",
        type=float,
        default=0.1,
        help="probability of missing credential",
    )
    parser.add_argument(
        "--invalid",
        type=float,
        default=0.1,
        help="probability of invalid credential",
    )
    parser.add_argument(
        "--rate-limit",
        dest="rate_limit",
        type=float,
        default=0.1,
        help="probability of rate limiting",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="random seed for reproducibility",
    )
    args = parser.parse_args()
    counts = simulate(
        args.requests,
        args.missing,
        args.invalid,
        args.rate_limit,
        seed=args.seed,
    )
    for code in sorted(counts):
        freq = counts[code]
        pct = freq / args.requests * 100
        print(f"{code}: {freq} ({pct:.1f}%)")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Simulate resource metrics and verify sampling error bounds.

Usage:
    uv run python scripts/resource_monitor_simulation.py --samples 50
"""
from __future__ import annotations

import argparse
import math
import random
import statistics
from typing import Iterable, List


def quantile(values: Iterable[float], q: float) -> float:
    """Return the linear-interpolated ``q``-quantile of ``values``."""
    data = sorted(values)
    k = (len(data) - 1) * q
    f = math.floor(k)
    c = math.ceil(k)
    if f == c:
        return data[int(k)]
    return data[f] * (c - k) + data[c] * (k - f)


def simulate(samples: int, mu: float, sigma: float, q: float) -> None:
    """Generate ``samples`` values and print stats after each draw."""
    data: List[float] = []
    for i in range(samples):
        data.append(random.gauss(mu, sigma))
        mean = statistics.mean(data)
        var = statistics.variance(data)
        q_val = quantile(data, q)
        se = math.sqrt(var / len(data))
        print(f"{i+1:3d} mean={mean:6.2f} var={var:6.2f} " f"q{q:.2f}={q_val:6.2f} se={se:6.2f}")
    error = abs(statistics.mean(data) - mu)
    bound = 1.96 * math.sqrt(statistics.variance(data) / len(data))
    print(f"error={error:.2f} bound={bound:.2f} within={error <= bound}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Simulate monitor statistics")
    parser.add_argument("--samples", type=int, default=50, help="number of draws")
    parser.add_argument("--mu", type=float, default=50.0, help="true mean")
    parser.add_argument("--sigma", type=float, default=10.0, help="true std dev")
    parser.add_argument("--quantile", type=float, default=0.95, help="quantile")
    args = parser.parse_args()
    simulate(args.samples, args.mu, args.sigma, args.quantile)


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    main()

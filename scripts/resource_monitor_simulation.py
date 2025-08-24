#!/usr/bin/env python3
"""Simulate resource metrics and verify sampling bounds.

Usage:
    uv run python scripts/resource_monitor_simulation.py --samples 100
"""

from __future__ import annotations

import argparse
import math
import random
import statistics


def simulate(samples: int, mu: float, sigma: float, p: float = 0.95) -> None:
    """Generate Gaussian samples and check statistical bounds.

    Args:
        samples: Number of observations to draw.
        mu: Mean of the underlying distribution.
        sigma: Standard deviation of the distribution.
        p: Quantile to evaluate, defaulting to 0.95.

    Raises:
        SystemExit: If the empirical statistics fall outside theoretical bounds.
    """

    if samples < 2:
        raise ValueError("samples must be >= 2")

    dist = statistics.NormalDist(mu, sigma)
    data: list[float] = []
    rng = random.Random()

    for i in range(1, samples + 1):
        val = rng.gauss(mu, sigma)
        data.append(val)
        mean = statistics.fmean(data)
        var = statistics.variance(data) if i > 1 else 0.0
        sorted_data = sorted(data)
        k = max(0, math.ceil(p * i) - 1)
        q = sorted_data[k]
        se_mean = math.sqrt(var / i) if i > 1 else float("inf")
        q_true = dist.inv_cdf(p)
        pdf_q = dist.pdf(q_true)
        se_q = math.sqrt(p * (1 - p) / (i * pdf_q * pdf_q)) if i > 1 else float("inf")
        mean_ok = abs(mean - mu) <= 3 * se_mean
        q_ok = abs(q - q_true) <= 3 * se_q
        print(
            f"{i:4d} mean={mean:.2f} var={var:.2f} "
            f"q{int(p * 100)}={q:.2f} SE_mean={se_mean:.2f} "
            f"SE_q={se_q:.2f} bounds={'ok' if mean_ok and q_ok else 'fail'}"
        )

    if not (mean_ok and q_ok):
        raise SystemExit("sampling bounds not satisfied")


def main() -> None:
    parser = argparse.ArgumentParser(description="Gaussian resource simulation")
    parser.add_argument("--samples", type=int, default=100, help="number of samples")
    parser.add_argument("--mu", type=float, default=50.0, help="mean of distribution")
    parser.add_argument(
        "--sigma",
        type=float,
        default=10.0,
        help="standard deviation of distribution",
    )
    args = parser.parse_args()
    simulate(args.samples, args.mu, args.sigma)


if __name__ == "__main__":
    main()

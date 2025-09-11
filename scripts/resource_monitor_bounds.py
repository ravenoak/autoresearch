#!/usr/bin/env python3
"""Compute resource monitor sampling interval and thresholds.

Usage:
    uv run python scripts/resource_monitor_bounds.py --load 0.5
"""
from __future__ import annotations

import argparse


def compute_interval(load: float, f_base: float, f_max: float, l_thresh: float) -> float:
    """Return sampling interval based on load.

    Args:
        load: Current CPU load fraction in [0, 1].
        f_base: Baseline sampling frequency.
        f_max: Maximum allowed frequency.
        l_thresh: Load threshold where scaling begins.
    """
    if not 0 <= load <= 1:
        raise SystemExit("load must be between 0 and 1")
    if f_base <= 0 or f_max <= 0 or l_thresh <= 0:
        raise SystemExit("frequencies and threshold must be positive")
    f = min(f_max, f_base * (1 + load / l_thresh))
    return 1 / f


def compute_threshold(mu: float, sigma: float, k: float = 2.0) -> float:
    """Return spike threshold using mean ``mu`` and std dev ``sigma``."""
    if sigma < 0:
        raise SystemExit("sigma must be non-negative")
    return mu + k * sigma


def main() -> None:
    parser = argparse.ArgumentParser(description="Derive monitor formulae")
    parser.add_argument("--load", type=float, default=0.5, help="CPU load fraction")
    parser.add_argument("--mu-cpu", type=float, default=0.5, help="mean CPU usage")
    parser.add_argument("--sigma-cpu", type=float, default=0.1, help="CPU std dev")
    parser.add_argument("--mu-mem", type=float, default=100.0, help="mean memory MB")
    parser.add_argument("--sigma-mem", type=float, default=10.0, help="memory std dev")
    args = parser.parse_args()
    interval = compute_interval(args.load, 1.0, 10.0, 0.7)
    cpu_th = compute_threshold(args.mu_cpu, args.sigma_cpu)
    mem_th = compute_threshold(args.mu_mem, args.sigma_mem)
    print(
        f"interval={interval:.3f}s cpu_threshold={cpu_th:.2f} mem_threshold={mem_th:.2f}"
    )


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    main()

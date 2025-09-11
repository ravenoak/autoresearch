#!/usr/bin/env python3
"""Compute task distribution and failure overhead.

Usage:
    uv run python scripts/distributed_coordination_formulas.py --tasks 9 --workers 4
"""
from __future__ import annotations

import argparse
from typing import List


def round_robin(tasks: int, workers: int) -> List[int]:
    """Return tasks per worker for round-robin scheduling."""
    if tasks < 0 or workers <= 0:
        raise SystemExit("tasks must be >= 0 and workers > 0")
    base, rem = divmod(tasks, workers)
    return [base + (1 if i < rem else 0) for i in range(workers)]


def failure_overhead(p: float) -> float:
    """Return multiplicative overhead factor for failure probability ``p``."""
    if not 0 <= p < 1:
        raise SystemExit("p must be in [0,1)")
    return 1 / (1 - p)


def main() -> None:
    parser = argparse.ArgumentParser(description="Derive coordination formulas")
    parser.add_argument("--tasks", type=int, default=10, help="total tasks")
    parser.add_argument("--workers", type=int, default=3, help="number of workers")
    parser.add_argument("--fail", type=float, default=0.1, help="failure probability")
    args = parser.parse_args()
    distribution = round_robin(args.tasks, args.workers)
    overhead = failure_overhead(args.fail)
    print(f"distribution={distribution} overhead={overhead:.2f}")


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    main()

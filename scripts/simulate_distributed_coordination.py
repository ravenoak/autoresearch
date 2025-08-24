#!/usr/bin/env python3
"""Demonstrate distributed scheduling throughput using multiple processes.

Usage:
    uv run python scripts/simulate_distributed_coordination.py --workers 2
"""

from __future__ import annotations

import argparse
import time
from concurrent.futures import ProcessPoolExecutor


def _square(x: int) -> int:
    """Return the square of ``x``."""

    return x * x


def main(workers: int, tasks: int) -> None:
    """Run a simple distributed simulation.

    Args:
        workers: Number of worker processes.
        tasks: How many integers to square per loop.
    """

    if workers <= 0 or tasks <= 0:
        raise SystemExit("workers and tasks must be positive")

    start = time.perf_counter()
    with ProcessPoolExecutor(max_workers=workers) as executor:
        for _ in range(10):
            list(executor.map(_square, range(tasks)))
    duration = time.perf_counter() - start
    print(f"Processed {tasks * 10} tasks in {duration:.3f}s " f"with {workers} workers")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Distributed coordination demo")
    parser.add_argument("--workers", type=int, default=2, help="number of workers")
    parser.add_argument("--tasks", type=int, default=100, help="tasks per loop")
    args = parser.parse_args()
    main(args.workers, args.tasks)

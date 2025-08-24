#!/usr/bin/env python3
"""Demonstrate distributed scheduling throughput.

Usage:
    uv run python scripts/simulate_distributed_coordination.py --workers 2
"""

from __future__ import annotations

import argparse
import time

from autoresearch.config.models import ConfigModel, DistributedConfig
from autoresearch.distributed import ProcessExecutor


def _square(x: int) -> int:
    """Return the square of ``x``."""

    return x * x


def main(workers: int, tasks: int) -> None:
    """Run a simple distributed simulation.

    Args:
        workers: Number of worker processes.
        tasks: How many integers to square per loop.
    """

    config = ConfigModel(
        distributed=True,
        distributed_config=DistributedConfig(enabled=True, num_cpus=workers),
    )
    executor = ProcessExecutor(config)
    start = time.perf_counter()
    for _ in range(10):
        executor.run_query(_square, range(tasks))
    duration = time.perf_counter() - start
    print(f"Processed {tasks * 10} tasks in {duration:.3f}s with {workers} workers")
    executor.shutdown()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Distributed coordination demo")
    parser.add_argument("--workers", type=int, default=2, help="number of workers")
    parser.add_argument("--tasks", type=int, default=100, help="tasks per loop")
    args = parser.parse_args()
    main(args.workers, args.tasks)


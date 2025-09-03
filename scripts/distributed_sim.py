#!/usr/bin/env python3
"""Simulate message throughput and resource consumption.

Usage:
    uv run python scripts/distributed_sim.py --workers 2 --messages 100

The simulation routes synthetic messages through multiple worker processes and
records throughput along with CPU and memory usage.
"""

from __future__ import annotations

import argparse
import json
import time
from concurrent.futures import ProcessPoolExecutor

from autoresearch.resource_monitor import ResourceMonitor


def _handle_message(n: int) -> int:
    """Perform trivial work to simulate message handling."""

    return n * n


def run_simulation(workers: int, messages: int, loops: int = 10) -> dict[str, float]:
    """Process messages across processes and gather performance metrics.

    Args:
        workers: Number of worker processes.
        messages: Messages handled per loop.
        loops: Scheduling loops to execute.

    Returns:
        Dictionary with total messages, duration, throughput, CPU percentage, and
        memory usage.
    """

    if workers <= 0 or messages <= 0 or loops <= 0:
        raise SystemExit("workers, messages, and loops must be positive")

    monitor = ResourceMonitor(interval=0.05)
    monitor.start()
    start = time.perf_counter()
    with ProcessPoolExecutor(max_workers=workers) as executor:
        for _ in range(loops):
            list(executor.map(_handle_message, range(messages)))
    duration = time.perf_counter() - start
    monitor.stop()

    total_messages = messages * loops
    throughput = total_messages / duration if duration > 0 else float("inf")
    cpu = float(monitor.cpu_gauge._value.get())
    mem = float(monitor.mem_gauge._value.get())
    return {
        "messages": float(total_messages),
        "duration_s": duration,
        "throughput": throughput,
        "cpu_percent": cpu,
        "memory_mb": mem,
    }


def main(workers: int, messages: int, loops: int = 10) -> dict[str, float]:
    """Run the simulation and print summary metrics."""

    metrics = run_simulation(workers=workers, messages=messages, loops=loops)
    print(
        f"Processed {int(metrics['messages'])} messages in "
        f"{metrics['duration_s']:.3f}s with {workers} workers"
    )
    print(
        json.dumps(
            {
                "throughput": metrics["throughput"],
                "cpu_percent": metrics["cpu_percent"],
                "memory_mb": metrics["memory_mb"],
            }
        )
    )
    return metrics


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Distributed message throughput simulation")
    parser.add_argument("--workers", type=int, default=2, help="number of worker processes")
    parser.add_argument("--messages", type=int, default=100, help="messages per scheduling loop")
    parser.add_argument("--loops", type=int, default=10, help="scheduling loops")
    args = parser.parse_args()
    main(args.workers, args.messages, args.loops)

#!/usr/bin/env python3
"""Simulate queue growth for stalled streaming clients.

Usage:
    uv run scripts/queue_growth_sim.py --rate 5 --size 1024 --stall 10
"""
from __future__ import annotations

import argparse
import asyncio


def simulate(rate: float, size: int, stall: float) -> tuple[int, int]:
    """Return queue length and approximate memory use."""
    produced = int(rate * stall)
    items = [b"x" * size for _ in range(produced)]
    queue: asyncio.Queue[bytes] = asyncio.Queue()
    for item in items:
        queue.put_nowait(item)
    memory = produced * size
    return queue.qsize(), memory


def main() -> None:
    parser = argparse.ArgumentParser(description="Model queue growth under stalled clients.")
    parser.add_argument("--rate", type=float, default=5.0, help="messages per second")
    parser.add_argument("--size", type=int, default=1024, help="bytes per message")
    parser.add_argument("--stall", type=float, default=10.0, help="seconds without consumption")
    args = parser.parse_args()
    length, memory = simulate(args.rate, args.size, args.stall)
    print(f"queue length: {length} items")
    print(f"approx memory: {memory} bytes")


if __name__ == "__main__":
    main()

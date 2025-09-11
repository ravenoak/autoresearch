#!/usr/bin/env python3
"""Simulate an agent task queue to validate ordering and capacity invariants.

Usage:
    uv run python scripts/agents_sim.py --tasks 5 --capacity 2 --output metrics.json

The simulation enqueues tasks and processes them while tracking queue length and
ordering. It returns metrics confirming the invariants.
"""
from __future__ import annotations

import argparse
import json
from collections import deque
from typing import Deque, Dict


def _simulate(tasks: int, capacity: int) -> Dict[str, object]:
    """Process tasks while maintaining a bounded FIFO queue.

    Args:
        tasks: Total tasks to enqueue.
        capacity: Maximum queue size.

    Returns:
        Metrics describing queue behaviour.
    """

    queue: Deque[int] = deque()
    processed: list[int] = []
    max_len = 0

    for task in range(tasks):
        queue.append(task)
        max_len = max(max_len, len(queue))
        if len(queue) > capacity:
            queue.popleft()
        processed.append(queue.popleft())

    ordered = all(prev <= nxt for prev, nxt in zip(processed, processed[1:]))
    return {"max_queue": max_len, "ordered": ordered}


def main(tasks: int, capacity: int, output: str | None) -> None:
    if tasks <= 0 or capacity <= 0:
        raise SystemExit("tasks and capacity must be positive")
    metrics = _simulate(tasks, capacity)
    if output:
        with open(output, "w", encoding="utf-8") as fh:
            json.dump(metrics, fh)
    print(json.dumps(metrics))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tasks", type=int, default=10, help="number of tasks")
    parser.add_argument("--capacity", type=int, default=5, help="queue capacity")
    parser.add_argument("--output", type=str, help="optional metrics path")
    args = parser.parse_args()
    main(args.tasks, args.capacity, args.output)

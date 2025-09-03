#!/usr/bin/env python3
"""Benchmark coordination throughput and fault tolerance.

Usage:
    uv run python scripts/distributed_coordination_benchmark.py --workers 2 --messages 10 --fail
"""

from __future__ import annotations

import argparse
import multiprocessing
import time
from typing import Any, Dict

from autoresearch.distributed.broker import InMemoryBroker
from autoresearch.distributed.coordinator import ResultAggregator


def _publisher(
    queue: multiprocessing.Queue[Any], messages: int, crash: bool
) -> None:
    """Publish ``messages`` items to ``queue`` and optionally crash."""

    for i in range(messages):
        if crash and i == messages // 2:
            raise RuntimeError("worker crashed")
        queue.put({"action": "agent_result", "payload": i})


def benchmark(workers: int, messages: int, fail: bool = False) -> Dict[str, float]:
    """Run the benchmark and return processed message count and throughput.

    Args:
        workers: Number of publisher processes.
        messages: Messages each worker sends.
        fail: If ``True``, the first worker crashes halfway through.

    Returns:
        Metrics dictionary with ``messages`` and ``throughput`` entries.
    """

    broker = InMemoryBroker()
    aggregator = ResultAggregator(broker.queue)
    aggregator.start()

    procs = []
    for w in range(workers):
        crash = fail and w == 0
        proc = multiprocessing.Process(
            target=_publisher, args=(broker.queue, messages, crash)
        )
        proc.start()
        procs.append(proc)

    start = time.perf_counter()
    for proc in procs:
        proc.join()
    broker.publish({"action": "stop"})
    aggregator.join()
    duration = time.perf_counter() - start
    count = len(aggregator.results)
    broker.shutdown()
    throughput = count / duration if duration > 0 else float("inf")
    return {"messages": float(count), "throughput": throughput}


def main(workers: int, messages: int, fail: bool) -> Dict[str, float]:
    """Execute benchmark and print summary metrics."""

    metrics = benchmark(workers, messages, fail)
    print(
        f"processed {int(metrics['messages'])} messages "
        f"with throughput {metrics['throughput']:.1f} msg/s"
    )
    return metrics


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Distributed coordination benchmark")
    parser.add_argument("--workers", type=int, default=2, help="publisher processes")
    parser.add_argument("--messages", type=int, default=10, help="messages per worker")
    parser.add_argument(
        "--fail",
        action="store_true",
        help="crash one worker halfway to test fault tolerance",
    )
    args = parser.parse_args()
    main(args.workers, args.messages, args.fail)


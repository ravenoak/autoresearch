"""Validate Redis-backed coordination via a simple simulation."""

from __future__ import annotations

import threading
import time
from typing import List

import pytest

pytestmark = [
    pytest.mark.slow,
    pytest.mark.requires_distributed,
    pytest.mark.redis,
]


def run_redis_simulation(
    redis_client,
    workers: int,
    tasks: int,
    network_latency: float,
    task_time: float,
    fail_worker: bool = False,
) -> dict[str, float]:
    """Execute a Redis-based coordination simulation and return metrics."""
    redis_client.flushdb()
    for i in range(tasks):
        redis_client.rpush("tasks", i)

    results: List[int] = []
    lock = threading.Lock()

    def worker(idx: int) -> None:
        processed = 0
        while True:
            item = redis_client.blpop(["tasks"], timeout=1)
            if item is None:
                break
            time.sleep(network_latency)
            time.sleep(task_time)
            with lock:
                results.append(int(item[1]))
            processed += 1
            if fail_worker and idx == 0 and processed >= tasks // workers:
                return

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(workers)]
    start = time.perf_counter()
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    duration = time.perf_counter() - start
    throughput = len(results) / duration if duration else float("inf")
    return {"tasks": float(len(results)), "duration_s": duration, "throughput": throughput}


def test_throughput_matches_theory(redis_client) -> None:
    """Measured throughput follows 1/(task_time + latency) per worker."""
    metrics = run_redis_simulation(
        redis_client,
        workers=2,
        tasks=60,
        network_latency=0.05,
        task_time=0.01,
    )
    expected = 2 / (0.05 + 0.01)
    assert metrics["throughput"] <= expected
    assert metrics["throughput"] > expected * 0.5


def test_failure_recovery(redis_client) -> None:
    """Remaining workers drain the queue when one stops processing."""
    metrics = run_redis_simulation(
        redis_client,
        workers=3,
        tasks=30,
        network_latency=0.0,
        task_time=0.005,
        fail_worker=True,
    )
    assert metrics["tasks"] == 30

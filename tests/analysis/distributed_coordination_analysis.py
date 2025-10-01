"""Simulate coordination overhead with ResourceMonitor."""

from __future__ import annotations

import json
import time
from multiprocessing import Process, Queue
from pathlib import Path
from typing import TypedDict

from prometheus_client import CollectorRegistry

from autoresearch.resource_monitor import ResourceMonitor


class ResourceMetrics(TypedDict):
    """CPU and memory metrics captured from the monitor."""

    cpu_percent: float
    memory_mb: float


def _worker(duration: float, queue: Queue[float]) -> None:
    """Busy loop to simulate work for ``duration`` seconds."""
    start = time.time()
    while time.time() - start < duration:
        sum(i * i for i in range(1000))
    queue.put(time.time() - start)


def simulate(node_count: int = 1, duration: float = 0.5) -> ResourceMetrics:
    """Run workers and capture CPU and memory metrics."""
    registry = CollectorRegistry()
    monitor = ResourceMonitor(interval=0.05, registry=registry)
    monitor.start()
    queue: Queue[float] = Queue()
    try:
        procs = [
            Process(target=_worker, args=(duration, queue))
            for _ in range(node_count)
        ]
        for proc in procs:
            proc.start()
        for proc in procs:
            proc.join()
        monitor.stop()
        cpu = float(monitor.cpu_gauge._value.get())
        mem = float(monitor.mem_gauge._value.get())
        return ResourceMetrics(cpu_percent=cpu, memory_mb=mem)
    finally:
        queue.close()
        queue.join_thread()


def run() -> dict[int, ResourceMetrics]:
    """Execute simulations for 1, 2, and 4 nodes."""
    results: dict[int, ResourceMetrics] = {}
    for count in (1, 2, 4):
        results[count] = simulate(node_count=count)
    out_path = Path(__file__).with_name("distributed_metrics.json")
    out_path.write_text(json.dumps(results, indent=2))
    return results


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))

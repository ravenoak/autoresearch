"""Orchestrator performance modeling and micro-benchmarks.

Provides queueing-theory metrics and a simple scheduling benchmark to
estimate throughput and resource usage.
"""

from __future__ import annotations

import cProfile
import io
import math
import pstats
import resource
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Dict


def queue_metrics(workers: int, arrival_rate: float, service_rate: float) -> Dict[str, float]:
    """Return utilization and average queue length for an M/M/c queue.

    Args:
        workers: Number of worker threads processing tasks.
        arrival_rate: Average rate that tasks arrive (tasks/s).
        service_rate: Average rate a worker completes tasks (tasks/s).

    Returns:
        Dictionary with utilization and expected queue length.

    Raises:
        ValueError: If any argument is non-positive or system is unstable.
    """
    if workers <= 0:
        raise ValueError("workers must be positive")
    if arrival_rate <= 0 or service_rate <= 0:
        raise ValueError("rates must be positive")

    rho = arrival_rate / (workers * service_rate)
    if rho >= 1:
        raise ValueError("system is unstable; utilization >= 1")

    ratio = arrival_rate / service_rate
    sum_terms = sum((ratio**n) / math.factorial(n) for n in range(workers))
    last = (ratio**workers) / (math.factorial(workers) * (1 - rho))
    p0 = 1 / (sum_terms + last)
    lq = (p0 * (ratio**workers) * rho) / (math.factorial(workers) * (1 - rho) ** 2)
    return {"utilization": rho, "avg_queue_length": lq}


def simulate(
    workers: int,
    arrival_rate: float,
    service_rate: float,
    tasks: int,
    mem_per_task: float,
) -> Dict[str, float]:
    """Combine queue metrics with a simple memory model.

    Args:
        workers: Number of worker threads.
        arrival_rate: Task arrival rate (tasks/s).
        service_rate: Per-worker service rate (tasks/s).
        tasks: Number of outstanding tasks.
        mem_per_task: Memory consumed by each task in megabytes.

    Returns:
        Dictionary with queue metrics and expected memory usage.
    """
    metrics = queue_metrics(workers, arrival_rate, service_rate)
    metrics["expected_memory"] = tasks * mem_per_task
    return metrics


def benchmark_scheduler(
    workers: int,
    tasks: int,
    mem_per_task: float = 0.0,
    profile: bool = False,
) -> Dict[str, float]:
    """Measure scheduling throughput and resource usage.

    Each task allocates memory and sleeps briefly to mimic an I/O-bound
    workload that releases the GIL, allowing throughput to scale with the number
    of workers.

    Args:
        workers: Number of worker threads to schedule tasks.
        tasks: Total number of tasks to dispatch.
        mem_per_task: Megabytes of memory to allocate per task.
        profile: Whether to return cProfile statistics for the run.

    Returns:
        Dictionary with observed throughput in tasks/s, CPU time, memory usage
        in kilobytes, and optional profiler output.

    Raises:
        ValueError: If ``workers`` or ``tasks`` is not positive.
    """
    if workers <= 0:
        raise ValueError("workers must be positive")
    if tasks <= 0:
        raise ValueError("tasks must be positive")

    profiler: cProfile.Profile | None = None
    if profile:
        profiler = cProfile.Profile()
        profiler.enable()

    start_res = resource.getrusage(resource.RUSAGE_SELF)
    start = time.perf_counter()

    def _workload(_: int) -> None:
        buf = bytearray(int(mem_per_task * 1024 * 1024))
        time.sleep(0.001)
        del buf

    with ThreadPoolExecutor(max_workers=workers) as exe:
        list(exe.map(_workload, range(tasks)))

    elapsed = time.perf_counter() - start
    end_res = resource.getrusage(resource.RUSAGE_SELF)

    profile_output = ""
    if profiler is not None:
        profiler.disable()
        buffer = io.StringIO()
        pstats.Stats(profiler, stream=buffer).sort_stats("cumulative").print_stats(5)
        profile_output = buffer.getvalue()

    throughput = tasks / elapsed if elapsed > 0 else float("inf")
    cpu_time = end_res.ru_utime - start_res.ru_utime
    mem_kb = end_res.ru_maxrss - start_res.ru_maxrss
    return {
        "throughput": throughput,
        "cpu_time": cpu_time,
        "mem_kb": mem_kb,
        "profile": profile_output,
    }

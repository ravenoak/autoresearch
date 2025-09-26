"""Orchestrator performance modeling and micro-benchmarks.

Provides queueing-theory metrics and a simple scheduling benchmark to
estimate throughput and resource usage.
"""

from __future__ import annotations

import cProfile
import io
import math
import statistics
import pstats
import resource
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from typing import Dict

# Tunable parameters to keep the benchmark representative yet stable.
#
# Sleep duration mimics an I/O-bound task that briefly releases the GIL so
# additional workers can make progress.
_SLEEP_DURATION = 0.001
# Require each measurement batch to last at least this long to amortize thread
# start-up overhead and scheduling jitter.
_MIN_MEASURE_DURATION = 0.05
# Gather multiple throughput samples per worker count to smooth transient noise
# without stretching overall runtime excessively.
_THROUGHPUT_SAMPLES = 3


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


@dataclass
class BenchmarkResult:
    """Performance metrics from a scheduling benchmark.

    Attributes:
        throughput: Observed throughput in tasks per second.
        cpu_time: User CPU time consumed in seconds.
        mem_kb: Resident memory usage in kilobytes.
        profile: Aggregated profiler statistics.
        throughput_samples: Individual throughput samples used to compute the
            aggregate throughput.
    """

    throughput: float
    cpu_time: float
    mem_kb: float
    profile: str = ""
    throughput_samples: tuple[float, ...] = field(default_factory=tuple)


def benchmark_scheduler(
    workers: int,
    tasks: int,
    mem_per_task: float = 0.0,
    profile: bool = False,
) -> BenchmarkResult:
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
        BenchmarkResult containing throughput in tasks/s, CPU time, memory usage
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

    effective_tasks = tasks
    estimated_task_time = tasks * _SLEEP_DURATION
    if estimated_task_time < _MIN_MEASURE_DURATION:
        effective_tasks *= math.ceil(
            _MIN_MEASURE_DURATION / max(estimated_task_time, _SLEEP_DURATION)
        )

    def _warmup(_: int) -> None:
        time.sleep(0)

    def _workload(_: int) -> None:
        if mem_per_task > 0:
            buf = bytearray(int(mem_per_task * 1024 * 1024))
        else:
            buf = None
        time.sleep(_SLEEP_DURATION)
        if buf is not None:
            del buf

    throughput_samples: list[float] = []
    with ThreadPoolExecutor(max_workers=workers) as exe:
        list(exe.map(_warmup, range(workers)))

        start_res = resource.getrusage(resource.RUSAGE_SELF)
        for _ in range(_THROUGHPUT_SAMPLES):
            iter_start = time.perf_counter()
            list(exe.map(_workload, range(effective_tasks)))
            elapsed = time.perf_counter() - iter_start
            throughput_samples.append(
                effective_tasks / elapsed if elapsed > 0 else float("inf")
            )
        end_res = resource.getrusage(resource.RUSAGE_SELF)

    profile_output = ""
    if profiler is not None:
        profiler.disable()
        buffer = io.StringIO()
        pstats.Stats(profiler, stream=buffer).sort_stats("cumulative").print_stats(5)
        profile_output = buffer.getvalue()

    throughput = statistics.median(throughput_samples)
    cpu_time = end_res.ru_utime - start_res.ru_utime
    mem_kb = end_res.ru_maxrss - start_res.ru_maxrss
    return BenchmarkResult(
        throughput=throughput,
        cpu_time=cpu_time,
        mem_kb=mem_kb,
        profile=profile_output,
        throughput_samples=tuple(throughput_samples),
    )

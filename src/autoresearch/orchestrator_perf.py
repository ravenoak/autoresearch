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
# additional workers can make progress. A longer delay keeps the benchmark
# dominated by simulated work instead of per-task overhead. Bumping the default
# to 8 ms makes the simulated workload heavy enough that multi-worker runs
# reliably outperform a single worker even after amortizing warm-up and
# scheduling overhead.
_SLEEP_DURATION = 0.008
# Require each worker's share of a measurement batch to last at least this long
# to amortize thread start-up overhead and scheduling jitter. The guard is
# scaled dynamically based on the estimated per-worker batch runtime. Raising
# the floor to 150 ms further suppresses noise so throughput scaling stays
# stable across platforms.
_MIN_MEASURE_DURATION = 0.15
# Gather multiple throughput samples per worker count to smooth transient noise
# without stretching overall runtime excessively.
_THROUGHPUT_SAMPLES = 3

# Public aliases used by CLI helpers to surface the tuned defaults.
DEFAULT_SLEEP_DURATION = _SLEEP_DURATION
DEFAULT_MIN_MEASURE_DURATION = _MIN_MEASURE_DURATION


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
    sleep_duration: float = _SLEEP_DURATION,
    min_measure_duration: float = _MIN_MEASURE_DURATION,
) -> BenchmarkResult:
    """Measure scheduling throughput and resource usage.

    Each task allocates memory and sleeps briefly to mimic an I/O-bound
    workload that releases the GIL, allowing throughput to scale with the number
    of workers. The benchmark adapts the number of scheduled tasks so each
    worker remains busy long enough to amortize scheduling overhead even as
    concurrency scales.

    Args:
        workers: Number of worker threads to schedule tasks.
        tasks: Total number of tasks to dispatch.
        mem_per_task: Megabytes of memory to allocate per task.
        profile: Whether to return cProfile statistics for the run.
        sleep_duration: Time each task blocks to simulate I/O (seconds).
        min_measure_duration: Minimum per-worker runtime for each measurement
            batch to amortize overhead (seconds).

    Returns:
        BenchmarkResult containing throughput in tasks/s, CPU time, memory usage
        in kilobytes, and optional profiler output.

    Raises:
        ValueError: If ``workers``, ``tasks``, ``sleep_duration``, or
            ``min_measure_duration`` is not positive.
    """
    if workers <= 0:
        raise ValueError("workers must be positive")
    if tasks <= 0:
        raise ValueError("tasks must be positive")
    if sleep_duration <= 0:
        raise ValueError("sleep_duration must be positive")
    if min_measure_duration <= 0:
        raise ValueError("min_measure_duration must be positive")

    profiler: cProfile.Profile | None = None
    if profile:
        profiler = cProfile.Profile()
        profiler.enable()

    # Estimate how long each worker will stay busy for a single measurement
    # batch. We require the per-worker runtime to exceed the amortization
    # target so throughput samples have comparable fidelity across worker
    # counts.
    min_workers = max(workers, 1)
    effective_tasks = max(tasks, 1)
    estimated_per_worker_runtime = (
        effective_tasks * sleep_duration
    ) / min_workers
    if estimated_per_worker_runtime < min_measure_duration:
        min_tasks_per_worker = math.ceil(min_measure_duration / sleep_duration)
        required_tasks = min_tasks_per_worker * min_workers
        effective_tasks = max(tasks, required_tasks)
        # Recompute to ensure the concurrency-aware guard is satisfied in case
        # rounding created a slight deficit.
        estimated_per_worker_runtime = (
            effective_tasks * sleep_duration
        ) / min_workers
        if estimated_per_worker_runtime < min_measure_duration:
            # Fallback to a loop in degenerate cases (e.g., very small sleep
            # durations) to avoid a silent infinite shortfall.
            while (
                (effective_tasks * sleep_duration) / min_workers
                < min_measure_duration
            ):
                effective_tasks += min_workers

    def _warmup(_: int) -> None:
        time.sleep(0)

    def _workload(_: int) -> None:
        if mem_per_task > 0:
            buf = bytearray(int(mem_per_task * 1024 * 1024))
        else:
            buf = None
        time.sleep(sleep_duration)
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

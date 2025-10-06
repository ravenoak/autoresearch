"""Micro-benchmark tests for scheduler resource usage."""

from __future__ import annotations

from collections import deque
from typing import Any, Iterable, Mapping, Sequence

import pytest

from autoresearch.orchestration.utils import enqueue_with_limit
from autoresearch.scheduler_benchmark import benchmark_scheduler

BenchmarkResult = tuple[float, int]
BenchmarkResults = Iterable[BenchmarkResult]


@pytest.fixture(scope="module")
def scheduler_memory_budget_kb(
    scheduler_benchmark_baseline: Mapping[str, Any]
) -> int:
    """Return the calibrated scheduler memory budget in kilobytes."""

    workers = scheduler_benchmark_baseline.get("workers", {})
    single_worker = workers.get("1", {})
    baseline_mem_mb = float(single_worker.get("expected_memory", 32.0))
    return int(baseline_mem_mb * 1024)


@pytest.fixture(scope="module")
def scheduler_cpu_overhead(
    scheduler_benchmark_baseline: Mapping[str, Any]
) -> float:
    """Return allowable CPU overhead derived from the throughput baseline."""

    workers = scheduler_benchmark_baseline.get("workers", {})
    single_worker = workers.get("1", {})
    throughput = float(single_worker.get("throughput", 120.0))
    return max(0.05, 1.0 / max(throughput, 1.0))


@pytest.mark.parametrize("duration", [0.01, 0.05, 0.1])
def test_benchmark_scheduler_resources(
    duration: float,
    scheduler_memory_budget_kb: int,
    scheduler_cpu_overhead: float,
) -> None:
    """Scheduler consumes minimal CPU time and memory."""
    cpu_time: float
    mem_kb: int
    cpu_time, mem_kb = benchmark_scheduler(duration)
    assert duration <= cpu_time <= duration + scheduler_cpu_overhead
    assert 0 <= mem_kb <= scheduler_memory_budget_kb * 2


def test_benchmark_scheduler_time_scales_with_duration(
    scheduler_memory_budget_kb: int,
) -> None:
    """CPU time is non-decreasing for longer durations."""
    durations: Sequence[float] = (0.01, 0.05, 0.1)
    results: BenchmarkResults = [benchmark_scheduler(d) for d in durations]
    cpu_times: list[float] = [cpu for cpu, _ in results]
    mem_usages: list[int] = [mem for _, mem in results]
    assert cpu_times == sorted(cpu_times)
    assert max(mem_usages) <= scheduler_memory_budget_kb * 2


def test_enqueue_with_limit_drops_items() -> None:
    """Queue drops items when the limit is reached."""
    q: deque[int] = deque()
    assert enqueue_with_limit(q, 1, 1) is True
    assert enqueue_with_limit(q, 2, 1) is False
    assert list(q) == [1]


def test_enqueue_with_limit_invalid_limit() -> None:
    """Invalid limits raise a ValueError."""
    q: deque[int] = deque()
    with pytest.raises(ValueError):
        enqueue_with_limit(q, 1, 0)

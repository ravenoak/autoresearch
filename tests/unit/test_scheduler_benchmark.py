"""Micro-benchmark tests for scheduler resource usage."""

from collections import deque
from typing import Iterable, Sequence

import pytest

from autoresearch.orchestration.utils import enqueue_with_limit
from autoresearch.scheduler_benchmark import benchmark_scheduler

BenchmarkResult = tuple[float, int]
BenchmarkResults = Iterable[BenchmarkResult]


@pytest.mark.parametrize("duration", [0.01, 0.05, 0.1])
def test_benchmark_scheduler_resources(duration: float) -> None:
    """Scheduler consumes minimal CPU time and memory."""
    cpu_time: float
    mem_kb: int
    cpu_time, mem_kb = benchmark_scheduler(duration)
    assert 0.0 <= cpu_time < 1.0
    assert 0 <= mem_kb < 50000


def test_benchmark_scheduler_time_scales_with_duration() -> None:
    """CPU time is non-decreasing for longer durations."""
    durations: Sequence[float] = (0.01, 0.05, 0.1)
    results: BenchmarkResults = [benchmark_scheduler(d) for d in durations]
    cpu_times: list[float] = [cpu for cpu, _ in results]
    mem_usages: list[int] = [mem for _, mem in results]
    assert cpu_times == sorted(cpu_times)
    assert max(mem_usages) < 50000


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

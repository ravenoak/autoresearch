"""Micro-benchmark tests for scheduler resource usage."""

from collections import deque

import pytest

from autoresearch.orchestration.utils import enqueue_with_limit
from autoresearch.scheduler_benchmark import benchmark_scheduler


@pytest.mark.parametrize("duration", [0.01, 0.05, 0.1])
def test_benchmark_scheduler_resources(duration: float) -> None:
    """Scheduler consumes minimal CPU time and memory."""
    cpu_time, mem_kb = benchmark_scheduler(duration)
    assert 0.0 <= cpu_time < 1.0
    assert 0 <= mem_kb < 50000


def test_benchmark_scheduler_time_scales_with_duration() -> None:
    """CPU time is non-decreasing for longer durations."""
    durations = [0.01, 0.05, 0.1]
    results = [benchmark_scheduler(d) for d in durations]
    cpu_times = [r[0] for r in results]
    mem_usages = [r[1] for r in results]
    assert cpu_times == sorted(cpu_times)
    assert max(mem_usages) < 50000


def test_enqueue_with_limit_drops_items() -> None:
    """Queue drops items when the limit is reached."""
    q = deque()
    assert enqueue_with_limit(q, 1, 1) is True
    assert enqueue_with_limit(q, 2, 1) is False
    assert list(q) == [1]


def test_enqueue_with_limit_invalid_limit() -> None:
    """Invalid limits raise a ValueError."""
    q = deque()
    with pytest.raises(ValueError):
        enqueue_with_limit(q, 1, 0)

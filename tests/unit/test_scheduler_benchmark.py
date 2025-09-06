"""Micro-benchmark tests for scheduler resource usage."""

from collections import deque

import pytest

from autoresearch.orchestration.utils import enqueue_with_limit
from autoresearch.scheduler_benchmark import benchmark_scheduler


def test_benchmark_scheduler_resources():
    """Scheduler consumes minimal CPU time and memory."""
    cpu_time, mem_kb = benchmark_scheduler(0.05)
    assert 0.0 <= cpu_time < 1.0
    assert 0 <= mem_kb < 50000


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

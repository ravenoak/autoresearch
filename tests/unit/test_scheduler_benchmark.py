"""Micro-benchmark tests for scheduler resource usage."""

from autoresearch.scheduler_benchmark import benchmark_scheduler


def test_benchmark_scheduler_resources():
    """Scheduler consumes minimal CPU time and memory."""
    cpu_time, mem_kb = benchmark_scheduler(0.05)
    assert 0.0 <= cpu_time < 1.0
    assert 0 <= mem_kb < 50000

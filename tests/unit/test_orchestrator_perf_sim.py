"""Tests for orchestrator performance simulation and benchmark."""

from autoresearch.orchestrator_perf import benchmark_scheduler, queue_metrics


def test_queue_metrics_more_workers():
    """Adding workers reduces expected queue length."""
    metrics_two = queue_metrics(2, 3, 5)
    metrics_four = queue_metrics(4, 3, 5)
    assert metrics_four["avg_queue_length"] < metrics_two["avg_queue_length"]


def test_benchmark_scheduler_scales():
    """Throughput increases with additional workers."""
    one = benchmark_scheduler(1, 100)
    two = benchmark_scheduler(2, 100)
    assert one["throughput"] > 0
    assert two["throughput"] > one["throughput"]
    assert one["cpu_time"] >= 0
    assert one["mem_kb"] >= 0

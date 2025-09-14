"""Tests for orchestrator performance simulation and benchmark."""

import pytest

from autoresearch.orchestrator_perf import benchmark_scheduler, queue_metrics, simulate


def test_queue_metrics_more_workers():
    """Adding workers reduces expected queue length."""
    metrics_two = queue_metrics(2, 3, 5)
    metrics_four = queue_metrics(4, 3, 5)
    assert metrics_four["avg_queue_length"] < metrics_two["avg_queue_length"]


def test_benchmark_scheduler_scales():
    """Throughput scales and profiling returns stats."""
    one = benchmark_scheduler(1, 50, profile=True)
    two = benchmark_scheduler(2, 50, profile=True)
    assert one["throughput"] > 0
    assert two["throughput"] > one["throughput"] * 1.2
    assert one["cpu_time"] >= 0
    assert one["mem_kb"] >= 0
    assert one["profile"]


def test_queue_metrics_mm1_values():
    """Queue metrics match analytic results for an M/M/1 system."""
    metrics = queue_metrics(1, 1, 2)
    assert metrics["utilization"] == 0.5
    assert metrics["avg_queue_length"] == pytest.approx(0.5, rel=1e-3)


def test_simulate_adds_memory_usage():
    """Simulation appends expected memory to queue metrics."""
    metrics = simulate(2, 3, 5, 10, 0.5)
    base = queue_metrics(2, 3, 5)
    assert metrics["utilization"] == base["utilization"]
    assert metrics["avg_queue_length"] == base["avg_queue_length"]
    assert metrics["expected_memory"] == 5.0

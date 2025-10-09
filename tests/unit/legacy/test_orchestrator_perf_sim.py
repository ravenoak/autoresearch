# mypy: ignore-errors
"""Tests for orchestrator performance simulation and benchmark."""

import json
import os
from pathlib import Path

import pytest

from autoresearch.orchestrator_perf import benchmark_scheduler, queue_metrics, simulate

REPO_ROOT = Path(__file__).resolve().parents[3]
BASELINE_SCHEDULER_PATH = (
    REPO_ROOT / "baseline" / "evaluation" / "scheduler_benchmark.json"
)
with BASELINE_SCHEDULER_PATH.open(encoding="utf-8") as scheduler_file:
    _SCHEDULER_BASELINE = json.load(scheduler_file)

BASELINE_ONE = _SCHEDULER_BASELINE["workers"]["1"]["throughput"]
BASELINE_TWO = _SCHEDULER_BASELINE["workers"]["2"]["throughput"]
BASELINE_RATIO = BASELINE_TWO / BASELINE_ONE


def test_queue_metrics_more_workers():
    """Adding workers reduces expected queue length."""
    metrics_two = queue_metrics(2, 3, 5)
    metrics_four = queue_metrics(4, 3, 5)
    assert metrics_four["avg_queue_length"] < metrics_two["avg_queue_length"]


@pytest.mark.skip(reason="Flaky performance test - depends on system load")
def test_benchmark_scheduler_scales():
    """Throughput scales and profiling returns stats.

    The scaling threshold can be adjusted with the
    ``SCHEDULER_SCALE_THRESHOLD`` environment variable. Baseline throughput is
    tunable via ``SCHEDULER_BASELINE_OPS``.
    """
    one = benchmark_scheduler(1, 50, profile=True)
    two = benchmark_scheduler(2, 50, profile=True)
    baseline = float(os.getenv("SCHEDULER_BASELINE_OPS", f"{BASELINE_ONE}"))
    threshold = float(
        os.getenv("SCHEDULER_SCALE_THRESHOLD", f"{BASELINE_RATIO * 0.9}")
    )
    assert one.throughput == pytest.approx(baseline, rel=0.25)
    assert two.throughput == pytest.approx(BASELINE_TWO, rel=0.25)
    assert two.throughput > one.throughput * threshold
    assert one.cpu_time >= 0
    assert one.mem_kb >= 0
    assert one.profile


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

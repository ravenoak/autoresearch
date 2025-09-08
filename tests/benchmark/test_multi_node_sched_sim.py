"""Benchmark multi-node scheduling with failure recovery."""

from __future__ import annotations

import pytest

from tests.benchmark.multi_node_sched_sim import run_simulation

pytestmark = [
    pytest.mark.slow,
    pytest.mark.requires_distributed,
    pytest.mark.requires_analysis,
]


def test_overhead_matches_theory() -> None:
    """Observed overhead aligns with the analytical 1/(1-p) model."""
    fail_rate = 0.2
    metrics = run_simulation(
        workers=3, tasks=300, network_latency=0.01, task_time=0.01, fail_rate=fail_rate
    )
    expected = 1 / (1 - fail_rate)
    assert metrics["overhead"] == pytest.approx(expected, rel=0.1)


def test_throughput_respects_worker_count() -> None:
    """Throughput increases with additional workers."""
    base = run_simulation(workers=2, tasks=200, network_latency=0.01, task_time=0.01, fail_rate=0.1)
    scaled = run_simulation(
        workers=4, tasks=200, network_latency=0.01, task_time=0.01, fail_rate=0.1
    )
    assert scaled["throughput"] > base["throughput"]

"""Validate assumptions about the distributed orchestrator simulation."""

from __future__ import annotations

import pytest

from scripts.distributed_orchestrator_sim import run_simulation

pytestmark = [pytest.mark.slow]


def test_throughput_scales_with_workers() -> None:
    """Throughput should increase with additional workers."""
    baseline = run_simulation(workers=1, tasks=20, network_latency=0.01, task_time=0.01)
    scaled = run_simulation(workers=2, tasks=20, network_latency=0.01, task_time=0.01)
    assert scaled["throughput"] > baseline["throughput"]
    assert scaled["avg_latency_s"] < baseline["avg_latency_s"]
    assert baseline["avg_latency_s"] >= 0.01


def test_invalid_args_raise_system_exit() -> None:
    """Invalid parameters terminate the simulation early."""
    with pytest.raises(SystemExit):
        run_simulation(workers=0, tasks=1)

"""Validate assumptions about the distributed orchestrator simulation."""

from __future__ import annotations

import pytest

from scripts.distributed_orchestrator_sim import run_simulation

pytestmark = [pytest.mark.slow]


def test_latency_matches_low_utilization() -> None:
    """Latency approaches network + service time when utilization is low."""
    metrics = run_simulation(
        workers=2, tasks=50, network_latency=0.05, task_time=0.005
    )
    assert metrics["avg_latency_s"] == pytest.approx(0.055, rel=1e-2)


def test_throughput_equals_arrival_rate() -> None:
    """Throughput equals the arrival rate for a stable system."""
    metrics = run_simulation(
        workers=2, tasks=20, network_latency=0.02, task_time=0.01
    )
    assert metrics["throughput"] == pytest.approx(50.0, rel=1e-6)


def test_invalid_args_raise_system_exit() -> None:
    """Invalid parameters terminate the simulation early."""
    with pytest.raises(SystemExit):
        run_simulation(workers=0, tasks=1)
    with pytest.raises(SystemExit):
        run_simulation(workers=1, tasks=10, network_latency=0.001, task_time=0.01)

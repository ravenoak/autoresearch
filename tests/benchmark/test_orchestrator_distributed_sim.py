"""Validate recovery metrics in the distributed orchestrator simulation."""

from __future__ import annotations

import pytest

from scripts.orchestrator_distributed_sim import run_simulation

pytestmark = [pytest.mark.slow]


def test_recovery_ratio_reflects_fail_rate() -> None:
    """Observed recovery ratio approximates the specified failure rate."""
    metrics = run_simulation(
        workers=2,
        tasks=50,
        network_latency=0.01,
        task_time=0.005,
        fail_rate=0.2,
    )
    assert metrics["recovery_ratio"] == pytest.approx(0.2, rel=0.5)


def test_invalid_parameters_raise() -> None:
    """Invalid arguments exit with an error."""
    with pytest.raises(SystemExit):
        run_simulation(workers=0, tasks=10)
    with pytest.raises(SystemExit):
        run_simulation(workers=1, tasks=10, fail_rate=1.0)

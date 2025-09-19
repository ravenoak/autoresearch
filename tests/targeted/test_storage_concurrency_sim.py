"""Targeted checks for the storage concurrency simulation."""

from __future__ import annotations

from scripts.storage_concurrency_sim import _run as run_simulation


def test_simulation_rejects_multiple_setups() -> None:
    """The simulation should initialize storage only once under load."""

    result = run_simulation(threads=4, items=2)

    assert result.setup_failures == 0
    assert result.setup_calls == 1
    assert result.unique_contexts == 1
    assert result.remaining_nodes == 0

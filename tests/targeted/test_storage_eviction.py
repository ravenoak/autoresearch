"""Targeted tests for RAM-budget eviction with concurrent writes."""

from scripts.storage_eviction_sim import run_simulation


def test_concurrent_eviction(config) -> None:
    """All claims are evicted when memory is above the budget."""
    config.ram_budget_mb = 1
    remaining = run_simulation(budget=1, workers=4, claims=5)
    assert remaining == 0

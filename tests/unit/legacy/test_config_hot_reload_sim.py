# mypy: ignore-errors
"""Run config hot reload simulation."""

import logging

from scripts.config_hot_reload_sim import simulate_reload


def test_config_hot_reload_sim() -> None:
    """Simulation converges to last valid configuration."""
    final = simulate_reload([1, 2, 3, 4])
    assert final == 4


def test_invalid_update_logged(caplog) -> None:
    """Invalid updates should not change config and log a warning."""
    caplog.set_level(logging.WARNING)
    final = simulate_reload([2, 3, 4])
    assert final == 4
    assert any("Invalid config value: 3" in r.getMessage() for r in caplog.records)

"""Run config hot reload simulation."""

from scripts.config_hot_reload_sim import simulate_reload


def test_config_hot_reload_sim() -> None:
    """Simulation converges to last valid configuration."""
    final = simulate_reload([1, 2, 3, 4])
    assert final == 4

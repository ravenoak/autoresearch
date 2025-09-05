"""Tests for configuration hot reload simulation."""

from tests.analysis.config_hot_reload_analysis import run


def test_config_hot_reload_sim() -> None:
    metrics = run()
    assert metrics["original"] == 1
    assert metrics["reloaded"] == 2
    assert metrics["success"]

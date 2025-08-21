"""Tests for agent coordination simulation."""

from tests.analysis.agent_coordination_analysis import run


def test_agent_coordination() -> None:
    metrics = run()
    assert metrics["final"] == metrics["expected"]
    assert metrics["success"]

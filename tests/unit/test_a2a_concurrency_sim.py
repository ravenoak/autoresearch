"""Validate A2A concurrency simulation against dispatch invariants.

See docs/specs/a2a-interface.md for invariants.
"""

from scripts.a2a_concurrency_sim import run_simulation


def test_simulation_counts() -> None:
    """Simulation dispatches tasks without races."""
    agents = 4
    tasks = 10
    result = run_simulation(agents, tasks)
    assert result.total_dispatched == agents * tasks
    assert sum(result.agent_counts.values()) == agents * tasks
    assert all(count == tasks for count in result.agent_counts.values())

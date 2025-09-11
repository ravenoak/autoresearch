from scripts.agents_sim import _simulate


def test_agents_sim_preserves_order_and_capacity():
    """Queue ordering and capacity invariants hold."""
    metrics = _simulate(tasks=5, capacity=2)
    assert metrics["ordered"] is True
    assert metrics["max_queue"] <= 2

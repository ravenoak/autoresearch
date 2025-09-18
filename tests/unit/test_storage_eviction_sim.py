import time
from unittest.mock import patch

from scripts.storage_eviction_sim import StorageManager, _run


def _fast_persist(claim: dict) -> None:
    StorageManager.get_graph().add_node(claim["id"], **claim)
    StorageManager.state.lru[claim["id"]] = time.time()


def test_eviction_removes_nodes_when_over_budget():
    """Normal scenario evicts all nodes above the RAM budget."""
    with patch("scripts.storage_eviction_sim.StorageManager.persist_claim", _fast_persist):
        remaining, _ = _run(
            threads=2, items=2, policy="lru", scenario="normal", return_metrics=True
        )
    assert remaining == 0


def test_under_budget_keeps_nodes():
    """Nodes persist when usage never exceeds the budget."""
    threads, items = 2, 2
    with patch("scripts.storage_eviction_sim.StorageManager.persist_claim", _fast_persist):
        remaining, _ = _run(
            threads=threads,
            items=items,
            policy="lru",
            scenario="under_budget",
            return_metrics=True,
        )
    assert remaining == threads * items


def test_zero_budget_disables_eviction():
    """Zero budget turns off eviction and retains nodes."""
    with patch("scripts.storage_eviction_sim.StorageManager.persist_claim", _fast_persist):
        remaining, _ = _run(
            threads=1,
            items=2,
            policy="lru",
            scenario="zero_budget",
            return_metrics=True,
        )
    assert remaining == 2


def test_deterministic_override_enforces_cap():
    """Explicit deterministic override bounds the graph despite unknown usage."""
    with patch("scripts.storage_eviction_sim.StorageManager.persist_claim", _fast_persist):
        remaining, _ = _run(
            threads=2,
            items=2,
            policy="lru",
            scenario="deterministic_override",
            return_metrics=True,
        )
    assert remaining == 1

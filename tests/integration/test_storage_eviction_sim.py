"""Verify storage eviction simulation aligns with implementation."""

from __future__ import annotations

import importlib.util
from pathlib import Path

from autoresearch.orchestration.metrics import EVICTION_COUNTER


def _load_sim_module():
    path = Path(__file__).resolve().parents[2] / "scripts" / "storage_eviction_sim.py"
    spec = importlib.util.spec_from_file_location("storage_eviction_sim", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load storage_eviction_sim module")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


sim = _load_sim_module()


def test_normal_scenario_eviction() -> None:
    """High usage triggers eviction leaving no nodes."""

    remaining = sim._run(threads=2, items=2, policy="lru", scenario="normal")
    assert remaining == 0


def test_zero_budget_keeps_nodes() -> None:
    """Zero budget disables eviction."""

    start = EVICTION_COUNTER._value.get()
    remaining = sim._run(threads=1, items=3, policy="lru", scenario="zero_budget")
    assert remaining == 3
    assert EVICTION_COUNTER._value.get() == start


def test_under_budget_keeps_nodes() -> None:
    """Usage below budget preserves all persisted nodes."""

    remaining = sim._run(threads=2, items=1, policy="lru", scenario="under_budget")
    assert remaining == 2


def test_no_nodes_scenario() -> None:
    """Enforcing the budget on an empty graph is a no-op."""

    remaining = sim._run(threads=2, items=2, policy="lru", scenario="no_nodes")
    assert remaining == 0


def test_deterministic_override_caps_graph() -> None:
    """Deterministic override bounds the graph even when usage metrics are absent."""

    remaining = sim._run(
        threads=2,
        items=2,
        policy="lru",
        scenario="deterministic_override",
    )
    assert remaining == 1

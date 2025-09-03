"""Unit tests for storage eviction simulation."""

import sys
from importlib.machinery import SourceFileLoader
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2] / "src"))


def load() -> object:
    path = Path(__file__).resolve().parents[2] / "scripts" / "storage_eviction_sim.py"
    return SourceFileLoader("storage_eviction_sim", str(path)).load_module()


def test_storage_eviction_sim() -> None:
    sim = load()
    scenarios = [
        "normal",
        "race",
        "zero_budget",
        "negative_budget",
        "under_budget",
        "no_nodes",
    ]
    results = {
        s: (
            sim._run(
                threads=2,
                items=2,
                policy="lru",
                scenario=s,
                jitter=0.0,
                evictors=2,
            )
            if s == "race"
            else sim._run(threads=2, items=2, policy="lru", scenario=s, jitter=0.0)
        )
        for s in scenarios
    }
    assert results["normal"] == 0
    assert results["race"] == 0
    assert results["zero_budget"] == 4
    assert results["negative_budget"] == 4
    assert results["under_budget"] == 4
    assert results["no_nodes"] == 0

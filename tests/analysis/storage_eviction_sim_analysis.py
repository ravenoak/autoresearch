"""Analysis helper for storage eviction simulation."""

import sys
from importlib.machinery import SourceFileLoader
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2] / "src"))


def run() -> dict[str, int]:
    path = Path(__file__).resolve().parents[2] / "scripts" / "storage_eviction_sim.py"
    sim = SourceFileLoader("storage_eviction_sim", str(path)).load_module()
    scenarios = [
        "normal",
        "race",
        "zero_budget",
        "negative_budget",
        "under_budget",
        "no_nodes",
        "exact_budget",
        "burst",
    ]
    results: dict[str, int] = {}
    for s in scenarios:
        kwargs = dict(threads=3, items=3, policy="lru", scenario=s, jitter=0.0)
        if s in {"race", "burst"}:
            kwargs["evictors"] = 2
        results[s] = sim._run(**kwargs)
    return results

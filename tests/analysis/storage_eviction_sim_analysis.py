
"""Analysis helper for storage eviction simulation."""

from importlib.machinery import SourceFileLoader
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2] / "src"))


def run() -> dict[str, int]:
    sim = SourceFileLoader(
        "storage_eviction_sim", "scripts/storage_eviction_sim.py"
    ).load_module()
    scenarios = ["normal", "race", "zero_budget"]
    return {
        s: sim._run(threads=3, items=3, policy="lru", scenario=s, jitter=0.0)
        for s in scenarios
    }

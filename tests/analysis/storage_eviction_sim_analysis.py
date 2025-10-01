"""Analysis helper for storage eviction simulation."""

import sys
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from types import ModuleType

sys.path.append(str(Path(__file__).resolve().parents[2] / "src"))


def _load_module(name: str, path: Path) -> ModuleType:
    spec = spec_from_file_location(name, path)
    if spec and spec.loader:
        module = module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    raise ImportError(name)


def run() -> dict[str, int]:
    path = Path(__file__).resolve().parents[2] / "scripts" / "storage_eviction_sim.py"
    sim = _load_module("storage_eviction_sim", path)
    scenarios = [
        "normal",
        "race",
        "zero_budget",
        "negative_budget",
        "under_budget",
        "no_nodes",
        "exact_budget",
        "burst",
        "deterministic_override",
    ]
    results: dict[str, int] = {}
    for s in scenarios:
        kwargs = dict(threads=3, items=3, policy="lru", scenario=s, jitter=0.0)
        if s in {"race", "burst"}:
            kwargs["evictors"] = 2
        results[s] = sim._run(**kwargs)
    return results

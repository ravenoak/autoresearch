#!/usr/bin/env python3
"""Simulate sequential writes enforcing the RAM budget.

Usage:
    uv run python scripts/ram_budget_enforcement_sim.py --items 5
"""

from __future__ import annotations

import argparse
from collections.abc import Callable

from autoresearch.config.loader import ConfigLoader
from autoresearch.config.models import ConfigModel, StorageConfig
from autoresearch.storage import StorageContext, StorageManager, StorageState


def _run(items: int) -> int:
    """Persist claims and return remaining node count after eviction."""

    cfg = ConfigModel(
        storage=StorageConfig(duckdb_path=":memory:"),
        ram_budget_mb=1,
        graph_eviction_policy="lru",
    )
    loader = ConfigLoader.new_for_tests()
    loader._config = cfg

    st = StorageState()
    ctx = StorageContext()
    StorageManager.state = st
    StorageManager.context = ctx

    original: Callable[[], float] = StorageManager._current_ram_mb
    StorageManager._current_ram_mb = staticmethod(lambda: 1000.0)
    try:
        StorageManager.setup(db_path=":memory:", context=ctx, state=st)
        for i in range(items):
            StorageManager.persist_claim({"id": f"c{i}", "type": "fact", "content": "c"})
            StorageManager._enforce_ram_budget(cfg.ram_budget_mb)
        remaining = StorageManager.get_graph().number_of_nodes()
    finally:
        StorageManager.teardown(remove_db=True, context=ctx, state=st)
        StorageManager.state = StorageState()
        StorageManager.context = StorageContext()
        StorageManager._current_ram_mb = staticmethod(original)
        ConfigLoader.reset_instance()

    return remaining


def main(items: int) -> None:
    if items <= 0:
        raise SystemExit("items must be positive")
    remaining = _run(items)
    print(f"nodes remaining after eviction: {remaining}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--items", type=int, default=5, help="items to persist")
    args = parser.parse_args()
    main(args.items)

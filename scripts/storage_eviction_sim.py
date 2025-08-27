#!/usr/bin/env python3
"""Simulate concurrent writers that stress `_enforce_ram_budget`.

Usage:
    uv run python scripts/storage_eviction_sim.py --threads 5
"""

from __future__ import annotations

import argparse
from threading import Thread

from autoresearch.config.loader import ConfigLoader
from autoresearch.config.models import ConfigModel, StorageConfig
from autoresearch.storage import StorageContext, StorageManager, StorageState


def _run(threads: int) -> int:
    """Persist claims concurrently and return remaining node count."""

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

    original = StorageManager._current_ram_mb
    StorageManager._current_ram_mb = staticmethod(lambda: 1000)
    try:
        StorageManager.setup(db_path=":memory:", context=ctx, state=st)

        def persist(idx: int) -> None:
            StorageManager.persist_claim(
                {"id": f"c{idx}", "type": "fact", "content": "c"}
            )
            StorageManager._enforce_ram_budget(cfg.ram_budget_mb)

        threads_list = [Thread(target=persist, args=(i,)) for i in range(threads)]
        for t in threads_list:
            t.start()
        for t in threads_list:
            t.join()

        remaining = StorageManager.get_graph().number_of_nodes()
    finally:
        StorageManager.teardown(remove_db=True, context=ctx, state=st)
        StorageManager.state = StorageState()
        StorageManager.context = StorageContext()
        StorageManager._current_ram_mb = original  # type: ignore[assignment]
        ConfigLoader.reset_instance()

    return remaining


def main(threads: int) -> None:
    if threads <= 0:
        raise SystemExit("threads must be positive")
    remaining = _run(threads)
    print(f"nodes remaining after eviction: {remaining}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--threads", type=int, default=5, help="concurrent writers")
    args = parser.parse_args()
    main(args.threads)

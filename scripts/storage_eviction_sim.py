#!/usr/bin/env python3
"""Simulate concurrent writers that stress `_enforce_ram_budget`.

Usage:
    uv run python scripts/storage_eviction_sim.py --threads 5 --items 5 \
        --policy lru --scenario normal

Scenarios:
    normal       concurrent writers with usage above the budget
    zero_budget  budget set to zero disables eviction
    under_budget memory usage below the budget keeps all nodes
    no_nodes     enforce budget when the graph is empty
"""

from __future__ import annotations

import argparse
from threading import Thread

from autoresearch.config.loader import ConfigLoader
from autoresearch.config.models import ConfigModel, StorageConfig
from autoresearch.storage import StorageContext, StorageManager, StorageState


def _run(threads: int, items: int, policy: str, scenario: str) -> int:
    """Persist claims concurrently and return remaining node count."""

    cfg = ConfigModel(
        storage=StorageConfig(duckdb_path=":memory:"),
        ram_budget_mb=0 if scenario == "zero_budget" else 1,
        graph_eviction_policy=policy,
    )
    loader = ConfigLoader.new_for_tests()
    loader._config = cfg

    st = StorageState()
    ctx = StorageContext()
    StorageManager.state = st
    StorageManager.context = ctx

    original = StorageManager._current_ram_mb
    current = 0 if scenario == "under_budget" else 1000
    StorageManager._current_ram_mb = staticmethod(lambda: current)
    try:
        StorageManager.setup(db_path=":memory:", context=ctx, state=st)

        def persist(idx: int) -> None:
            for j in range(items):
                StorageManager.persist_claim({
                    "id": f"c{idx}-{j}",
                    "type": "fact",
                    "content": "c",
                })
                StorageManager._enforce_ram_budget(cfg.ram_budget_mb)

        if scenario == "no_nodes":
            StorageManager._enforce_ram_budget(cfg.ram_budget_mb)
        else:
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


VALID_POLICIES = {"lru", "score", "hybrid", "adaptive", "priority"}
SCENARIOS = {"normal", "zero_budget", "under_budget", "no_nodes"}


def main(threads: int, items: int, policy: str, scenario: str) -> None:
    if threads <= 0 or items <= 0:
        raise SystemExit("threads and items must be positive")
    if policy not in VALID_POLICIES:
        allowed = ", ".join(sorted(VALID_POLICIES))
        raise SystemExit(f"policy must be one of: {allowed}")
    if scenario not in SCENARIOS:
        allowed = ", ".join(sorted(SCENARIOS))
        raise SystemExit(f"scenario must be one of: {allowed}")
    remaining = _run(threads, items, policy, scenario)
    print(f"nodes remaining after eviction: {remaining}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--threads", type=int, default=5, help="concurrent writers")
    parser.add_argument("--items", type=int, default=5, help="items per thread")
    parser.add_argument(
        "--policy",
        type=str,
        default="lru",
        help="eviction policy",
    )
    parser.add_argument(
        "--scenario",
        type=str,
        default="normal",
        help="simulation scenario",
    )
    args = parser.parse_args()
    main(args.threads, args.items, args.policy.lower(), args.scenario.lower())

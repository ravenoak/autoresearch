#!/usr/bin/env python3
"""Simulate concurrent writers that stress `_enforce_ram_budget`.

Usage:
    uv run python scripts/storage_eviction_sim.py --threads 5 --items 5 \
        --policy lru --scenario normal --evictors 2

Scenarios:
    normal           concurrent writers with usage above the budget
    zero_budget      budget set to zero disables eviction
    negative_budget  negative budget disables eviction
    under_budget     memory usage below the budget keeps all nodes
    exact_budget     usage equals the budget and eviction is skipped
    no_nodes         enforce budget when the graph is empty
    race             dedicated eviction threads run alongside writers
    burst            writers omit enforcement; separate evictors run
"""

from __future__ import annotations

import argparse
import time
from threading import Event, Thread

from autoresearch.config.loader import ConfigLoader
from autoresearch.config.models import ConfigModel, StorageConfig
from autoresearch.storage import StorageContext, StorageManager, StorageState


def _run(
    threads: int,
    items: int,
    policy: str,
    scenario: str,
    jitter: float = 0.0,
    evictors: int = 0,
) -> int:
    """Persist claims concurrently and return remaining node count."""

    cfg = ConfigModel(
        storage=StorageConfig(duckdb_path=":memory:"),
        ram_budget_mb=0 if scenario in {"zero_budget", "negative_budget"} else 1,
        graph_eviction_policy=policy,
    )
    loader = ConfigLoader.new_for_tests()
    loader._config = cfg

    st = StorageState()
    ctx = StorageContext()
    StorageManager.state = st
    StorageManager.context = ctx

    original = StorageManager._current_ram_mb
    current = (
        0
        if scenario == "under_budget"
        else cfg.ram_budget_mb if scenario == "exact_budget" else 1000
    )
    StorageManager._current_ram_mb = staticmethod(lambda: current)
    stop = Event()

    enforce_budget = -1 if scenario == "negative_budget" else cfg.ram_budget_mb

    try:
        StorageManager.setup(db_path=":memory:", context=ctx, state=st)

        def persist(idx: int) -> None:
            for j in range(items):
                StorageManager.persist_claim(
                    {
                        "id": f"c{idx}-{j}",
                        "type": "fact",
                        "content": "c",
                    }
                )
                if scenario != "burst":
                    StorageManager._enforce_ram_budget(enforce_budget)
                if jitter:
                    time.sleep(jitter)

        def enforce() -> None:
            while not stop.is_set():
                StorageManager._enforce_ram_budget(enforce_budget)
                time.sleep(jitter or 0.001)

        if scenario == "no_nodes":
            StorageManager._enforce_ram_budget(enforce_budget)
        else:
            threads_list = [Thread(target=persist, args=(i,)) for i in range(threads)]
            evictor_threads = [Thread(target=enforce) for _ in range(evictors)]
            if scenario in {"race", "burst"} and not evictor_threads:
                evictor_threads = [Thread(target=enforce)]
            for ev in evictor_threads:
                ev.start()
            for t in threads_list:
                t.start()
            for t in threads_list:
                t.join()
            for ev in evictor_threads:
                stop.set()
                ev.join()
            if scenario == "burst":
                StorageManager._enforce_ram_budget(enforce_budget)

        remaining = StorageManager.get_graph().number_of_nodes()
    finally:
        StorageManager.teardown(remove_db=True, context=ctx, state=st)
        StorageManager.state = StorageState()
        StorageManager.context = StorageContext()
        StorageManager._current_ram_mb = original  # type: ignore[assignment]
        ConfigLoader.reset_instance()

    return remaining


VALID_POLICIES = {"lru", "score", "hybrid", "adaptive", "priority"}
SCENARIOS = {
    "normal",
    "zero_budget",
    "negative_budget",
    "under_budget",
    "exact_budget",
    "no_nodes",
    "race",
    "burst",
}


def main(
    threads: int,
    items: int,
    policy: str,
    scenario: str,
    jitter: float,
    evictors: int,
) -> None:
    if threads <= 0 or items <= 0:
        raise SystemExit("threads and items must be positive")
    if policy not in VALID_POLICIES:
        allowed = ", ".join(sorted(VALID_POLICIES))
        raise SystemExit(f"policy must be one of: {allowed}")
    if scenario not in SCENARIOS:
        allowed = ", ".join(sorted(SCENARIOS))
        raise SystemExit(f"scenario must be one of: {allowed}")
    if jitter < 0:
        raise SystemExit("jitter must be non-negative")
    remaining = _run(threads, items, policy, scenario, jitter, evictors)
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
    parser.add_argument(
        "--jitter",
        type=float,
        default=0.0,
        help="sleep between writes to model contention",
    )
    parser.add_argument(
        "--evictors",
        type=int,
        default=0,
        help="dedicated eviction threads",
    )
    args = parser.parse_args()
    main(
        args.threads,
        args.items,
        args.policy.lower(),
        args.scenario.lower(),
        args.jitter,
        args.evictors,
    )

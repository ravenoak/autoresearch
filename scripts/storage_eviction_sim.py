#!/usr/bin/env python3
"""Simulate concurrent writers that stress `_enforce_ram_budget`.

Usage:
    uv run python scripts/storage_eviction_sim.py --threads 5 --items 5 \
        --policy lru --scenario normal --evictors 2

The simulation reports the remaining nodes, runtime, and approximate
throughput.

Scenarios:
    normal           concurrent writers with usage above the budget
    zero_budget      budget set to zero disables eviction
    negative_budget  negative budget disables eviction
    under_budget     memory usage below the budget keeps all nodes
    exact_budget     usage equals the budget and eviction is skipped
    no_nodes         enforce budget when the graph is empty
    race             dedicated eviction threads run alongside writers
    burst            writers omit enforcement; separate evictors run
    deterministic_override
                     deterministic node cap enforces a hard limit despite
                     missing RAM metrics
    stale_lru        clears the LRU cache before enforcement to mimic stale
                     eviction metadata
    metrics_dropout  reproduces the Hypothesis seed
                     170090525894866085979644260693064061602 where RAM metrics
                     report a spike once and then fall to 0 MB
"""

from __future__ import annotations

import argparse
import random
import time
from threading import Event, Thread
from collections.abc import Callable
from typing import cast

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
    seed: int | None = None,
    return_metrics: bool = False,
) -> int | tuple[int, float]:
    """Persist claims concurrently.

    Args:
        threads: Number of writer threads.
        items: Items each thread should persist.
        policy: Eviction policy to use.
        scenario: Simulation scenario.
        jitter: Sleep between writes to model contention.
        evictors: Dedicated eviction threads.
        seed: Optional regression seed used by scenarios that require determinism.
        return_metrics: When ``True`` also return the runtime.

    Returns:
        Remaining node count and optionally the elapsed time in seconds.
    """

    deterministic_override = scenario == "deterministic_override"
    if scenario in {"zero_budget", "negative_budget"}:
        ram_budget = 0
    elif scenario == "metrics_dropout":
        ram_budget = 3
    else:
        ram_budget = 1

    cfg = ConfigModel(
        storage=StorageConfig(
            duckdb_path=":memory:",
            deterministic_node_budget=1 if deterministic_override else None,
        ),
        ram_budget_mb=ram_budget,
        graph_eviction_policy=policy,
    )
    loader = ConfigLoader.new_for_tests()
    loader._config = cfg
    ConfigLoader._instance = loader

    st = StorageState()
    ctx = StorageContext()
    StorageManager.state = st
    StorageManager.context = ctx

    original: Callable[[], float] = StorageManager._current_ram_mb
    scenario_seed = seed if seed is not None else DEFAULT_SCENARIO_SEEDS.get(scenario)
    rng = random.Random(scenario_seed % (2**32)) if scenario_seed is not None else None

    if scenario == "metrics_dropout":
        spike = cfg.ram_budget_mb * (2 + (rng.random() if rng else 1.0))
        readings = [spike] + [0.0] * 1024
        iterator = iter(readings)

        def _next_reading(iterator=iterator) -> float:
            return next(iterator, 0.0)

        StorageManager._current_ram_mb = staticmethod(_next_reading)
    else:
        current = (
            0
            if scenario in {"under_budget", "deterministic_override"}
            else (cfg.ram_budget_mb if scenario == "exact_budget" else 1000)
        )
        StorageManager._current_ram_mb = staticmethod(
            lambda current=current: float(current)
        )
    stop = Event()

    enforce_budget = -1 if scenario == "negative_budget" else cfg.ram_budget_mb

    start = time.perf_counter()
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
            if scenario == "stale_lru":
                StorageManager.state.lru.clear()
                StorageManager._enforce_ram_budget(enforce_budget)

        remaining = StorageManager.get_graph().number_of_nodes()
    finally:
        StorageManager.teardown(remove_db=True, context=ctx, state=st)
        StorageManager.state = StorageState()
        StorageManager.context = StorageContext()
        StorageManager._current_ram_mb = staticmethod(original)
        ConfigLoader.reset_instance()

    elapsed = time.perf_counter() - start
    if return_metrics:
        return remaining, elapsed
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
    "deterministic_override",
    "stale_lru",
    "metrics_dropout",
}

DEFAULT_SCENARIO_SEEDS = {
    "metrics_dropout": 170090525894866085979644260693064061602,
}


def main(
    threads: int,
    items: int,
    policy: str,
    scenario: str,
    jitter: float,
    evictors: int,
    seed: int | None,
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
    remaining, elapsed = cast(
        tuple[int, float],
        _run(
            threads,
            items,
            policy,
            scenario,
            jitter,
            evictors,
            seed,
            return_metrics=True,
        ),
    )
    total = threads * items
    rate = total / elapsed if elapsed else float("inf")
    print(f"nodes remaining after eviction: {remaining}")
    print(f"runtime: {elapsed:.3f} s")
    print(f"throughput: {rate:.1f} nodes/s")


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
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="optional regression seed for seeded scenarios",
    )
    args = parser.parse_args()
    main(
        args.threads,
        args.items,
        args.policy.lower(),
        args.scenario.lower(),
        args.jitter,
        args.evictors,
        args.seed,
    )

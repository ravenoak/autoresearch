#!/usr/bin/env python3
"""Simulate concurrent setup and writes while enforcing the RAM budget.

Usage:
    uv run python scripts/storage_concurrency_sim.py --threads 5 --items 10
"""

from __future__ import annotations

import argparse
from collections.abc import Callable
from dataclasses import dataclass
from threading import Barrier, BrokenBarrierError, Lock, Thread
from time import perf_counter

import autoresearch.storage as storage_module
from autoresearch.config.loader import ConfigLoader
from autoresearch.config.models import ConfigModel, StorageConfig
from autoresearch.storage import StorageContext, StorageManager, StorageState


@dataclass(slots=True)
class SimulationResult:
    """Capture concurrency metrics returned by :func:`_run`."""

    threads: int
    items: int
    setup_calls: int
    setup_failures: int
    unique_contexts: int
    setup_wall_time_ms: float
    persist_wall_time_ms: float
    remaining_nodes: int


def _run(threads: int, items: int) -> SimulationResult:
    """Persist claims concurrently and return detailed metrics."""

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

    original_ram: Callable[[], float] = StorageManager._current_ram_mb
    StorageManager._current_ram_mb = staticmethod(lambda: 1000.0)
    original_setup = storage_module.setup

    setup_calls = 0
    setup_lock = Lock()
    setup_contexts: list[StorageContext] = []
    setup_errors: list[BaseException] = []

    def counted_setup(*args, **kwargs):
        nonlocal setup_calls
        try:
            return original_setup(*args, **kwargs)
        finally:
            with setup_lock:
                setup_calls += 1

    setup_wall_time_ms = 0.0
    persist_wall_time_ms = 0.0
    remaining = 0

    storage_module.setup = counted_setup

    try:
        barrier = Barrier(threads)
        error_lock = Lock()

        def do_setup() -> None:
            try:
                barrier.wait()
            except BrokenBarrierError as exc:  # pragma: no cover - defensive
                with error_lock:
                    setup_errors.append(exc)
                return
            try:
                result = StorageManager.setup(
                    db_path=":memory:", context=ctx, state=st
                )
            except BaseException as exc:  # pragma: no cover - defensive
                with error_lock:
                    setup_errors.append(exc)
            else:
                with setup_lock:
                    setup_contexts.append(result)

        setup_threads = [
            Thread(target=do_setup) for _ in range(threads)
        ]
        setup_start = perf_counter()
        for thread in setup_threads:
            thread.start()
        for thread in setup_threads:
            thread.join()
        setup_wall_time_ms = (perf_counter() - setup_start) * 1000.0

        if setup_errors:
            errors = ", ".join(str(err) for err in setup_errors)
            raise RuntimeError(f"setup failed under concurrency: {errors}")

        def persist(idx: int) -> None:
            for j in range(items):
                StorageManager.persist_claim(
                    {"id": f"c{idx}-{j}", "type": "fact", "content": "c"}
                )
                StorageManager._enforce_ram_budget(cfg.ram_budget_mb)

        writer_threads = [
            Thread(target=persist, args=(i,)) for i in range(threads)
        ]
        persist_start = perf_counter()
        for thread in writer_threads:
            thread.start()
        for thread in writer_threads:
            thread.join()
        persist_wall_time_ms = (perf_counter() - persist_start) * 1000.0

        remaining = StorageManager.get_graph().number_of_nodes()
    finally:
        StorageManager.teardown(remove_db=True, context=ctx, state=st)
        StorageManager.state = StorageState()
        StorageManager.context = StorageContext()
        StorageManager._current_ram_mb = staticmethod(original_ram)
        ConfigLoader.reset_instance()
        storage_module.setup = original_setup

    unique_contexts = len({id(c) for c in setup_contexts}) if setup_contexts else 0

    return SimulationResult(
        threads=threads,
        items=items,
        setup_calls=setup_calls,
        setup_failures=len(setup_errors),
        unique_contexts=unique_contexts,
        setup_wall_time_ms=setup_wall_time_ms,
        persist_wall_time_ms=persist_wall_time_ms,
        remaining_nodes=remaining,
    )


def main(threads: int, items: int) -> None:
    if threads <= 0 or items <= 0:
        raise SystemExit("threads and items must be positive")
    result = _run(threads, items)
    print(f"setup calls: {result.setup_calls}")
    print(f"setup failures: {result.setup_failures}")
    print(f"unique contexts: {result.unique_contexts}")
    print(f"setup wall time (ms): {result.setup_wall_time_ms:.2f}")
    print(f"persist wall time (ms): {result.persist_wall_time_ms:.2f}")
    print(f"nodes remaining after eviction: {result.remaining_nodes}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--threads", type=int, default=5, help="concurrent writers")
    parser.add_argument("--items", type=int, default=10, help="items per thread")
    args = parser.parse_args()
    main(args.threads, args.items)

"""Simulate concurrent writes that trigger RAM-budget eviction.

Usage:
    uv run scripts/storage_eviction_sim.py --workers 4 --claims 10 --budget 1
"""

from __future__ import annotations

import argparse
import threading
from typing import Callable

from autoresearch.config.loader import ConfigLoader
from autoresearch.storage import StorageContext, StorageManager, StorageState


def _insert(start: int, count: int) -> None:
    """Persist a sequence of synthetic claims."""
    for i in range(start, start + count):
        StorageManager.persist_claim({"id": f"c{i}", "type": "t", "content": "x"})


def run_simulation(budget: int = 1, workers: int = 4, claims: int = 10) -> int:
    """Run the eviction simulation and return remaining graph nodes.

    Args:
        budget: RAM budget in megabytes.
        workers: Number of concurrent writer threads.
        claims: Number of claims per worker.
    """
    loader = ConfigLoader()
    loader.config.ram_budget_mb = budget
    ConfigLoader._instance = loader
    original: Callable[[], float] = StorageManager._current_ram_mb
    StorageManager._current_ram_mb = staticmethod(lambda: float(budget * 1000))
    ctx, st = StorageContext(), StorageState()
    StorageManager.setup(db_path=":memory:", context=ctx, state=st)
    threads = [threading.Thread(target=_insert, args=(n * claims, claims)) for n in range(workers)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    graph_nodes = (
        StorageManager.context.graph.number_of_nodes() if StorageManager.context.graph else 0
    )
    StorageManager.teardown(remove_db=True, context=ctx, state=st)
    StorageManager._current_ram_mb = original
    return graph_nodes


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workers", type=int, default=4, help="number of writer threads")
    parser.add_argument("--claims", type=int, default=10, help="claims per worker")
    parser.add_argument("--budget", type=int, default=1, help="RAM budget in MB")
    args = parser.parse_args()
    remaining = run_simulation(args.budget, args.workers, args.claims)
    print(f"final nodes={remaining}")


if __name__ == "__main__":
    main()

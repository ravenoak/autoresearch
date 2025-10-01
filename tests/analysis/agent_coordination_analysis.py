"""Simulate agents incrementing a shared counter with locking."""

from __future__ import annotations

import json
from multiprocessing import Lock as create_lock
from multiprocessing import Process, Value
from multiprocessing.sharedctypes import Synchronized
from multiprocessing.synchronize import Lock as SyncLock
from pathlib import Path
from typing import TYPE_CHECKING, cast


if TYPE_CHECKING:
    CounterValue = Synchronized[int]
else:  # pragma: no cover - runtime fallback
    CounterValue = Synchronized


def _worker(counter: CounterValue, lock: SyncLock, increments: int) -> None:
    """Increment ``counter`` safely using ``lock``."""
    for _ in range(increments):
        with lock:
            counter.value += 1


def simulate(workers: int = 4, increments: int = 1000) -> dict[str, int | bool]:
    """Run workers and validate the final counter value."""
    counter = cast(CounterValue, Value("i", 0))
    lock: SyncLock = create_lock()
    procs = [Process(target=_worker, args=(counter, lock, increments)) for _ in range(workers)]
    for p in procs:
        p.start()
    for p in procs:
        p.join()
    expected = workers * increments
    success = counter.value == expected
    out_path = Path(__file__).with_name("agent_coordination_metrics.json")
    out_path.write_text(
        json.dumps({"final": counter.value, "expected": expected, "success": success}, indent=2) + "\n"
    )
    return {"final": counter.value, "expected": expected, "success": success}


def run() -> dict[str, int | bool]:
    """Entry point for running the simulation."""
    return simulate()


if __name__ == "__main__":  # pragma: no cover
    print(json.dumps(run(), indent=2))

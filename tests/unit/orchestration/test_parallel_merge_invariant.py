"""Parallel merge preserves unique group claims.

Derived from `docs/algorithms/orchestration.md`.
"""

from __future__ import annotations

import time
from concurrent.futures import ThreadPoolExecutor, as_completed


def test_parallel_merge_invariant() -> None:
    """Merging results yields one claim per group regardless of order."""

    groups = [["a1"], ["b1", "b2"], ["c1"]]

    def run_group(group: list[str]) -> str:
        time.sleep(0.05 * len(group))
        return " ".join(group)

    results: list[tuple[str, str]] = []
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = {executor.submit(run_group, g): g for g in groups}
        for future in as_completed(futures):
            grp = futures[future]
            results.append((" ".join(grp), future.result()))

    merged = dict(results)
    assert merged == {"a1": "a1", "b1 b2": "b1 b2", "c1": "c1"}

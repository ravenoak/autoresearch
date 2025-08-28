#!/usr/bin/env python3
"""Simulate idempotent DuckDB schema creation.

Usage:
    uv run python scripts/schema_idempotency_sim.py --runs 3
"""

from __future__ import annotations

import argparse
from typing import List, Sequence, Tuple

from autoresearch.storage_backends import DuckDBStorageBackend


def _run(runs: int) -> List[Sequence[Tuple[str, ...]]]:
    """Execute repeated setup calls and record table listings."""

    backend = DuckDBStorageBackend()
    tables: List[Sequence[Tuple[str, ...]]] = []
    try:
        for _ in range(runs):
            backend.setup(db_path=":memory:")
            assert backend._conn is not None  # for type checkers
            rows = backend._conn.execute("SHOW TABLES").fetchall()
            tables.append(rows)
        return tables
    finally:
        backend.close()


def main(runs: int) -> None:
    if runs <= 0:
        raise SystemExit("runs must be positive")
    tables = _run(runs)
    first = tables[0]
    stable = all(t == first for t in tables[1:])
    status = "stable" if stable else "changed"
    print(f"schema {status} across {runs} runs")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runs", type=int, default=2, help="number of setup iterations")
    args = parser.parse_args()
    main(args.runs)

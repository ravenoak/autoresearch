#!/usr/bin/env python3
"""Simulate DuckDB backups and verify copy integrity.

Usage:
    uv run python scripts/storage_backup_sim.py --rows 10
"""

from __future__ import annotations

import argparse
import os
import shutil
import tempfile

import duckdb


def backup_and_compare(rows: int) -> bool:
    """Insert rows, create a backup, and check equality."""
    with tempfile.TemporaryDirectory() as tmpdir:
        src = os.path.join(tmpdir, "src.db")
        backup = os.path.join(tmpdir, "backup.db")
        conn = duckdb.connect(src)
        conn.execute("create table if not exists items(id integer, val text)")
        conn.executemany(
            "insert into items values (?, ?)",
            [(i, f"v{i}") for i in range(rows)],
        )
        conn.execute("checkpoint")
        shutil.copyfile(src, backup)
        src_rows = conn.execute("select * from items order by id").fetchall()
        conn.close()
        copy = duckdb.connect(backup)
        backup_rows = copy.execute("select * from items order by id").fetchall()
        copy.close()
        return src_rows == backup_rows


def main(rows: int) -> None:
    if rows <= 0:
        raise SystemExit("rows must be positive")
    ok = backup_and_compare(rows)
    status = "consistent" if ok else "mismatch"
    print(f"backup {status} for {rows} rows")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rows", type=int, default=5, help="rows to insert before backup")
    args = parser.parse_args()
    main(args.rows)

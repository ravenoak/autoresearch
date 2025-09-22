#!/usr/bin/env python3
"""Sync coverage.xml to baseline/coverage.xml and normalize metadata.

This helper copies the generated coverage XML to the baseline while keeping
permissions and timestamps consistent. It is idempotent and performs a
content-difference check before writing.

Usage:
    uv run python scripts/sync_coverage_baseline.py \
        [--source coverage.xml] \
        [--baseline baseline/coverage.xml]

Behavior:
- If the baseline file differs from the source, overwrite the baseline.
- Ensure both files (source and baseline) share the same file mode (permissions).
- Set both mtimes to the same value (the source file's mtime) for reproducibility.
"""
from __future__ import annotations

import argparse
import filecmp
import os
import shutil
from pathlib import Path


def sync_coverage(source: Path, baseline: Path) -> None:
    if not source.exists():
        raise FileNotFoundError(f"Source coverage file not found: {source}")

    baseline.parent.mkdir(parents=True, exist_ok=True)

    # Read source metadata upfront
    stat = source.stat()
    mode = stat.st_mode
    mtime = stat.st_mtime

    # Copy if different
    needs_copy = True
    if baseline.exists():
        try:
            needs_copy = not filecmp.cmp(source, baseline, shallow=False)
        except OSError:
            needs_copy = True
    if needs_copy:
        shutil.copyfile(source, baseline)

    # Align permissions for both files
    os.chmod(source, mode)
    os.chmod(baseline, mode)

    # Align timestamps (atime = mtime for determinism)
    os.utime(source, (mtime, mtime))
    os.utime(baseline, (mtime, mtime))


def main() -> int:
    parser = argparse.ArgumentParser(description="Sync coverage baseline file")
    parser.add_argument(
        "--source",
        type=Path,
        default=Path("coverage.xml"),
        help="Path to generated coverage XML",
    )
    parser.add_argument(
        "--baseline",
        type=Path,
        default=Path("baseline/coverage.xml"),
        help="Path to baseline coverage XML",
    )
    args = parser.parse_args()

    sync_coverage(args.source, args.baseline)
    print(f"Synchronized {args.source} -> {args.baseline}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())

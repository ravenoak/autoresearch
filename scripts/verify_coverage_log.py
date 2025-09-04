#!/usr/bin/env python3
"""Verify coverage progress log completion.

Usage:
    uv run python scripts/verify_coverage_log.py <log_file>

The script exits non-zero if the log is missing or lacks the 'DONE' marker.
"""
from __future__ import annotations

import sys
from pathlib import Path


def main(path: str) -> int:
    log_path = Path(path)
    if not log_path.exists():
        print(f"missing log file: {path}")
        return 1
    content = log_path.read_text(encoding="utf-8")
    if "DONE" not in content:
        print("coverage did not finish")
        return 1
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: verify_coverage_log.py <log_file>")
        raise SystemExit(1)
    raise SystemExit(main(sys.argv[1]))

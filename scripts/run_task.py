#!/usr/bin/env python3
"""Run Go Task commands with a graceful fallback.

Usage:
    uv run python scripts/run_task.py [TASK_ARGS...]

This wrapper checks that Go Task is installed before delegating to it.
"""
from __future__ import annotations

import shutil
import subprocess
import sys


def main(argv: list[str]) -> int:
    if shutil.which("task") is None:
        msg = (
            "Go Task is not installed. Install it from https://taskfile.dev/ "
            "or run scripts/setup.sh"
        )
        print(f"ERROR: {msg}", file=sys.stderr)
        return 1
    result = subprocess.run(["task", *argv])
    return result.returncode


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    raise SystemExit(main(sys.argv[1:]))

#!/usr/bin/env python3
"""Fail if code or tests change without spec updates.

Usage:
    uv run python scripts/check_spec_updated.py
"""
from __future__ import annotations

import subprocess
import sys


def staged_files() -> list[str]:
    result = subprocess.run(
        ["git", "diff", "--cached", "--name-only"],
        capture_output=True,
        text=True,
        check=False,
    )
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def main() -> int:
    files = staged_files()
    code_changed = any(f.startswith("src/") or f.startswith("tests/") for f in files)
    spec_changed = any(
        f.startswith("docs/specs/") or f == "docs/spec_template.md" for f in files
    )
    if code_changed and not spec_changed:
        print(
            "Code or tests changed without spec updates. Update docs/specs.",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Validate spec files against the canonical template.

Usage:
    uv run python scripts/lint_specs.py
"""
from __future__ import annotations

from pathlib import Path
import sys

REQUIRED_HEADINGS = [
    "## Overview",
    "## Algorithms",
    "## Invariants",
    "## Proof Sketch",
    "## Simulation Expectations",
    "## Traceability",
]


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    specs = list((root / "docs" / "specs").glob("*.md"))
    specs.append(root / "docs" / "spec_template.md")
    missing: dict[Path, list[str]] = {}
    for path in specs:
        if path.name == "README.md":
            continue
        text = path.read_text()
        missing_headings = [h for h in REQUIRED_HEADINGS if h not in text]
        if missing_headings:
            missing[path] = missing_headings
    if missing:
        for path, heads in missing.items():
            print(f"{path} missing headings: {', '.join(heads)}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

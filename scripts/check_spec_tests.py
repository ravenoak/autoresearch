#!/usr/bin/env python3
"""Ensure each spec in docs/specs references at least one test.

Usage:
    uv run python scripts/check_spec_tests.py
"""
from __future__ import annotations

import pathlib

SPEC_DIR = pathlib.Path(__file__).resolve().parent.parent / "docs" / "specs"


def main() -> int:
    missing: list[pathlib.Path] = []
    for path in SPEC_DIR.glob("*.md"):
        if path.name == "README.md":
            continue
        if "../../tests/" not in path.read_text():
            missing.append(path)
    if missing:
        print("Spec files missing test references:")
        for p in missing:
            print(f"- {p.relative_to(SPEC_DIR.parent.parent)}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

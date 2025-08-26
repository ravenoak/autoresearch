#!/usr/bin/env python3
"""Verify that each spec references existing tests.

Usage:
    uv run python scripts/check_spec_tests.py
"""
from __future__ import annotations

import pathlib
import re

SPEC_DIR = pathlib.Path(__file__).resolve().parent.parent / "docs" / "specs"
EXTRA_SPECS = [
    pathlib.Path(__file__).resolve().parent.parent
    / "docs"
    / "algorithms"
    / "storage_eviction.md",
]


def main() -> int:
    root = SPEC_DIR.parent.parent
    missing: dict[pathlib.Path, list[str]] = {}
    pattern = re.compile(r"\.\./\.\./tests/[\w/._-]+")
    spec_files = [p for p in SPEC_DIR.glob("*.md") if p.name != "README.md"]
    spec_files.extend(EXTRA_SPECS)
    for path in spec_files:
        text = path.read_text()
        refs = pattern.findall(text)
        bad = []
        for ref in refs:
            target = (path.parent / ref).resolve()
            if not target.exists():
                bad.append(ref)
        if not refs or bad:
            missing[path] = bad
    if missing:
        print("Spec files with missing test references:")
        for spec, refs in missing.items():
            print(f"- {spec.relative_to(root)}")
            for ref in refs:
                print(f"  {ref}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

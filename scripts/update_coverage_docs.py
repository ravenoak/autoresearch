#!/usr/bin/env python3
"""Update coverage numbers in STATUS.md and docs/release_plan.md.

Usage:
    uv run python scripts/update_coverage_docs.py [--file coverage.xml]
    uv run python scripts/update_coverage_docs.py --value 75.0
"""

from __future__ import annotations

import argparse
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FILES = [
    ROOT / "STATUS.md",
    ROOT / "docs" / "release_plan.md",
]

PATTERNS = [
    re.compile(r"(previous baseline was )\*\*\d+%\*\*"),
    re.compile(r"(coverage from the unit subset is )\*\*\d+%\*\*"),
    re.compile(r"(current coverage is )\*\*\d+%\*\*"),
    re.compile(r"(Total coverage is )\*\*\d+%\*\*"),
    re.compile(r"(currently reports )\*\*\d+%\*\*"),
    re.compile(r"(coverage noted at )\*\*\d+%\*\*"),
]

COVERAGE_WORD = re.compile(r"\b\d+% coverage\b")


def read_coverage(path: Path) -> int:
    """Return rounded line coverage percentage from a coverage XML file."""
    root = ET.parse(path).getroot()
    return round(float(root.attrib["line-rate"]) * 100)


def update_file(path: Path, coverage: int) -> None:
    """Replace coverage references in *path* with *coverage*."""
    text = path.read_text()
    for pattern in PATTERNS:
        text = pattern.sub(lambda m: f"{m.group(1)}**{coverage}%**", text)
    text = COVERAGE_WORD.sub(f"{coverage}% coverage", text)
    path.write_text(text)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Write coverage into docs")
    parser.add_argument(
        "--file", default="coverage.xml", type=Path, help="Coverage XML file to read"
    )
    parser.add_argument("--value", type=float, help="Override coverage percentage")
    args = parser.parse_args(argv)

    if args.value is not None:
        coverage = round(args.value)
    else:
        coverage = read_coverage(args.file)

    for file in FILES:
        update_file(file, coverage)

    print(f"Wrote coverage {coverage}% to {len(FILES)} files.")
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())

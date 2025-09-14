"""Verify documentation coverage values against the baseline and threshold.

Usage:
    uv run python scripts/check_coverage_docs.py [--baseline baseline/coverage.xml]
                                         [--minimum 90]
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path
from xml.etree import ElementTree as ET

FILES = [
    Path("STATUS.md"),
    Path("docs/release_plan.md"),
]

PATTERNS = [
    re.compile(r"(coverage from the unit subset is )\*\*(\d+)%\*\*"),
    re.compile(r"(current coverage is )\*\*(\d+)%\*\*"),
    re.compile(r"(Total coverage is )\*\*(\d+)%\*\*"),
    re.compile(r"(coverage noted at )\*\*(\d+)%\*\*"),
]


def read_coverage(path: Path) -> int:
    """Return rounded line coverage percentage from a coverage XML file."""
    tree = ET.parse(path)
    rate = float(tree.getroot().attrib.get("line-rate", 0.0))
    return round(rate * 100)


def extract_numbers(text: str) -> set[int]:
    """Collect coverage percentages from known patterns."""
    numbers: set[int] = set()
    for pattern in PATTERNS:
        for match in pattern.finditer(text):
            numbers.add(int(match.group(2)))
    numbers.update(int(n) for n in re.findall(r"(\d+)% coverage", text))
    return numbers


def check_files(files: list[Path], expected: int) -> list[str]:
    errors: list[str] = []
    for file in files:
        text = file.read_text()
        nums = extract_numbers(text)
        if not nums:
            errors.append(f"No coverage percentage found in {file}")
            continue
        if len(nums) > 1 or nums.pop() != expected:
            errors.append(f"Coverage mismatch in {file}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Ensure coverage docs match baseline and threshold"
    )
    parser.add_argument(
        "--baseline",
        default=Path("baseline/coverage.xml"),
        type=Path,
        help="Path to baseline coverage XML",
    )
    parser.add_argument(
        "--minimum",
        type=int,
        default=90,
        help="Minimum required coverage percentage",
    )
    args = parser.parse_args()
    coverage = read_coverage(args.baseline)
    if coverage < args.minimum:
        print(f"Coverage {coverage}% below required {args.minimum}%")  # pragma: no cover
        return 1
    errors = check_files(FILES, coverage)
    if errors:
        for msg in errors:
            print(msg)
        return 1
    print(f"Documentation coverage matches {coverage}%")
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    raise SystemExit(main())

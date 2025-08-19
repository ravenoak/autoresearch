#!/usr/bin/env python
"""Update project version in pyproject.toml and src/autoresearch/__init__.py.

Usage:
    uv run python scripts/bump_version.py 0.1.1
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

from packaging.version import InvalidVersion, Version

ROOT = Path(__file__).resolve().parents[1]
PYPROJECT = ROOT / "pyproject.toml"
INIT_FILE = ROOT / "src" / "autoresearch" / "__init__.py"


def _update_pyproject(version: str) -> None:
    content = PYPROJECT.read_text()
    new_content = re.sub(r'(?m)^version = "[^"]+"', f'version = "{version}"', content)
    PYPROJECT.write_text(new_content)


def _update_init(version: str) -> None:
    content = INIT_FILE.read_text()
    new_content = re.sub(r'__version__ = "[^"]+"', f'__version__ = "{version}"', content)
    INIT_FILE.write_text(new_content)


def main(argv: list[str] | None = None) -> int:
    """Validate version string and update project files."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("version", help="New version, e.g., 0.1.1")
    args = parser.parse_args(argv)

    try:
        Version(args.version)
    except InvalidVersion as exc:
        raise SystemExit(f"Invalid version '{args.version}': {exc}")

    _update_pyproject(args.version)
    _update_init(args.version)
    print(f"Version updated to {args.version}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

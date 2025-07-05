#!/usr/bin/env python3
"""Platform aware installer for Autoresearch.

This script checks basic platform requirements and installs optional
dependencies using Poetry. Pass ``--minimal`` to install only the
minimal optional dependencies. Without flags, all optional extras will
be installed.
"""

from __future__ import annotations

import argparse
import os
import platform
import subprocess
import sys
from pathlib import Path
from typing import List
import tomllib

MIN_VERSION = (3, 12)


def check_python() -> None:
    """Ensure the running Python meets the minimum version."""
    if sys.version_info < MIN_VERSION:
        sys.exit(
            f"Python {MIN_VERSION[0]}.{MIN_VERSION[1]}+ is required, "
            f"found {sys.version.split()[0]}"
        )


def run(cmd: List[str]) -> None:
    """Execute a command and exit on failure."""
    print(" ".join(cmd))
    subprocess.check_call(cmd)


def main() -> None:
    parser = argparse.ArgumentParser(description="Install Autoresearch")
    parser.add_argument(
        "--minimal",
        action="store_true",
        help="Install only minimal optional dependencies",
    )
    args = parser.parse_args()

    check_python()

    def get_all_extras() -> List[str]:
        data = tomllib.loads(Path("pyproject.toml").read_text())
        deps = data.get("project", {}).get("optional-dependencies", {})
        return list(deps.keys())

    # Select extras set
    extras = ["minimal"] if args.minimal else [e for e in get_all_extras() if e != "minimal"]

    # Ensure Poetry uses the current interpreter
    run(["poetry", "env", "use", sys.executable])

    cmd = ["poetry", "install", "--with", "dev", "--extras"] + extras
    run(cmd)

    print("Installation complete on", platform.platform())


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Platform aware installer for Autoresearch.

This utility simplifies installation by resolving optional dependencies
based on the arguments provided.  By default all extras are installed.
Use ``--minimal`` to only install the minimal extra or ``--extras`` to
specify a comma separated list as documented in ``docs/installation.md``.
The script ensures Poetry uses the running interpreter before invoking
``poetry install``.
"""

from __future__ import annotations

import argparse
import platform
import subprocess
import sys
from typing import List

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
        help="Install only the minimal extra",
    )
    parser.add_argument(
        "--extras",
        help="Comma separated extras to install (e.g. nlp,parsers)",
        default="",
    )
    args = parser.parse_args()

    check_python()

    # Determine extras set
    extras: List[str] = []
    if args.minimal:
        extras.append("minimal")
    if args.extras:
        extras.extend([e.strip() for e in args.extras.split(",") if e.strip()])
    if not extras:
        extras = ["full"]

    # Ensure Poetry uses the current interpreter
    run(["poetry", "env", "use", sys.executable])

    cmd = ["poetry", "install", "--with", "dev", "--extras"] + extras
    run(cmd)

    print("Installation complete on", platform.platform())


if __name__ == "__main__":
    main()

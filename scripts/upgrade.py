#!/usr/bin/env python3
"""Upgrade Autoresearch installation.

This script checks the Python version and updates the package using Poetry
when a ``pyproject.toml`` is present. Otherwise it falls back to ``pip``.
"""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path
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
    check_python()
    poetry = shutil.which("poetry")
    if poetry and Path("pyproject.toml").exists():
        run([poetry, "update", "autoresearch"])
    else:
        run([sys.executable, "-m", "pip", "install", "-U", "autoresearch"])


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Platform aware installer for Autoresearch.

This script checks basic platform requirements and installs optional
dependencies using Poetry. Pass ``--minimal`` to install only the
minimal optional dependencies. Without flags, optional extras are
resolved automatically and missing groups are installed. Use
``--upgrade`` to run ``poetry update`` on the environment after
installation.
"""

from __future__ import annotations

import argparse
import os
import platform
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Set
from importlib import metadata
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


def get_optional_dependencies() -> Dict[str, List[str]]:
    """Return the optional dependency groups from ``pyproject.toml``."""
    data = tomllib.loads(Path("pyproject.toml").read_text())
    return data.get("project", {}).get("optional-dependencies", {})


def get_installed_packages() -> Set[str]:
    """Return the names of packages installed in the current environment."""
    return {dist.metadata["Name"] for dist in metadata.distributions()}


def extract_name(requirement: str) -> str:
    """Extract the package name from a Poetry requirement string."""
    name = requirement.split()[0]
    return name.split("[")[0]


def main() -> None:
    parser = argparse.ArgumentParser(description="Install Autoresearch")
    parser.add_argument(
        "--minimal",
        action="store_true",
        help="Install only minimal optional dependencies",
    )
    parser.add_argument(
        "--upgrade",
        action="store_true",
        help="Run 'poetry update' after installation",
    )
    args = parser.parse_args()

    check_python()

    optional = get_optional_dependencies()
    installed = get_installed_packages()

    extras: List[str]
    if args.minimal:
        extras = ["minimal"]
    else:
        extras = []
        for name, pkgs in optional.items():
            if name == "minimal":
                continue
            pkg_names = [extract_name(p) for p in pkgs]
            if any(p not in installed for p in pkg_names):
                extras.append(name)

    # Ensure Poetry uses the current interpreter
    run(["poetry", "env", "use", sys.executable])

    cmd = ["poetry", "install", "--with", "dev"]
    if extras:
        cmd += ["--extras"] + extras
    run(cmd)

    if args.upgrade:
        run(["poetry", "update"])

    print("Installation complete on", platform.platform())


if __name__ == "__main__":
    main()

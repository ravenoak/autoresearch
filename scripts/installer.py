#!/usr/bin/env python3
"""Platform aware installer for Autoresearch.

The script installs missing optional dependencies using Poetry or pip.
It detects required extras from ``autoresearch.toml`` or from explicit
CLI flags. Pass ``--minimal`` to install only the ``minimal`` extras
group. Without flags it reads ``autoresearch.toml`` and inspects the
current environment to resolve missing extras automatically. Use
``--upgrade`` to update the base package with Poetry or pip depending on
the installation method.
"""

from __future__ import annotations

import argparse
import os
import platform
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Set
import shutil
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


def extras_from_config(cfg_path: Path) -> Set[str]:
    """Infer required extras from an ``autoresearch.toml`` file."""
    if not cfg_path.exists():
        return set()

    config = tomllib.loads(cfg_path.read_text())
    extras: Set[str] = set()

    search = config.get("search", {})
    context = search.get("context_aware", {})
    if any(
        context.get(k, False)
        for k in (
            "use_query_expansion",
            "use_entity_recognition",
            "use_topic_modeling",
        )
    ):
        extras.add("nlp")

    if search.get("use_semantic_similarity") or search.get("hybrid_query"):
        extras.add("nlp")

    local_file = search.get("local_file", {}).get("path")
    local_git = search.get("local_git", {}).get("repo_path")
    backends = search.get("backends", [])
    if local_file or local_git or any(b in {"local_file", "local_git"} for b in backends):
        extras.add("parsers")

    embed_backends = search.get("embedding_backends", [])
    if "duckdb" in embed_backends:
        extras.add("vss")

    if config.get("distributed", {}).get("enabled"):
        extras.add("distributed")

    duckdb = config.get("storage", {}).get("duckdb", {})
    if duckdb.get("vector_extension"):
        extras.add("vss")

    ui_cfg = config.get("ui") or config.get("gui") or {}
    core_cfg = config.get("core", {})
    interfaces = core_cfg.get("interfaces", [])
    if (
        isinstance(ui_cfg, dict) and ui_cfg.get("enabled")
    ) or core_cfg.get("enable_gui") or core_cfg.get("use_gui") or any(
        i in {"gui", "ui", "streamlit"} for i in (interfaces or [])
    ):
        extras.add("ui")

    return extras


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
        "--extras",
        default="",
        help="Comma separated extras to install in addition to auto-detected ones",
    )
    parser.add_argument(
        "--config",
        default="autoresearch.toml",
        help="Configuration file used for extras detection",
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

    detected: Set[str] = set()
    extras: Set[str] = set()

    if args.minimal:
        extras.add("minimal")
    else:
        detected.update(extras_from_config(Path(args.config)))
        for name, pkgs in optional.items():
            if name == "minimal":
                continue
            pkg_names = [extract_name(p) for p in pkgs]
            if any(p not in installed for p in pkg_names):
                detected.add(name)

    if args.extras:
        extras.update({e.strip() for e in args.extras.split(",") if e.strip()})

    extras.update(detected)
    extras = {e for e in extras if e in optional}

    poetry = shutil.which("poetry")
    use_poetry = poetry and Path("pyproject.toml").exists()

    if use_poetry:
        # Ensure Poetry uses the current interpreter
        run([poetry, "env", "use", sys.executable])

        cmd = [poetry, "install", "--with", "dev"]
        if extras:
            cmd += ["--extras"] + sorted(extras)
        run(cmd)

        if args.upgrade:
            run([poetry, "update"])
    else:
        package = "autoresearch"
        if extras:
            package += "[" + ",".join(sorted(extras)) + "]"
        cmd = [sys.executable, "-m", "pip", "install"]
        if args.upgrade:
            cmd.append("-U")
        cmd.append(package)
        run(cmd)

    print("Installation complete on", platform.platform())


if __name__ == "__main__":
    main()

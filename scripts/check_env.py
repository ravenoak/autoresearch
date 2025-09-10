#!/usr/bin/env python3
"""Check development tool versions.

Usage:
    uv run python scripts/check_env.py

Versions for optional extras are loaded from ``pyproject.toml``. Extra groups
can be specified via the ``EXTRAS`` environment variable.
"""
from __future__ import annotations

import argparse
import logging
import os
import re
import subprocess
import sys
import tomllib
import warnings
from dataclasses import dataclass
from importlib import metadata
from pathlib import Path

if sys.version_info < (3, 12):
    raise SystemExit(
        f"Python 3.12+ required, found {sys.version_info.major}.{sys.version_info.minor}"
    )

try:  # pragma: no cover - packaging is required
    from packaging.version import Version
    from packaging.requirements import Requirement
except ModuleNotFoundError as exc:  # pragma: no cover
    raise SystemExit("packaging library is required") from exc

BASE_REQUIREMENTS = {
    "python": "3.12.0",
    "task": "3.0.0",
    "uv": "0.7.0",
}

BASE_EXTRAS = ["dev-minimal", "test"]

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def extras_to_check() -> list[str]:
    """Return extras from ``EXTRAS`` env var in addition to base extras."""

    env_extras = os.environ.get("EXTRAS", "").split()
    return sorted(set(BASE_EXTRAS + env_extras))


REPO_ROOT = Path(__file__).resolve().parents[1]  # repository root
PYPROJECT_PATH = REPO_ROOT / "pyproject.toml"


def load_extra_requirements(extras_to_check: list[str]) -> dict[str, str]:
    """Return versions for packages from specified extras in pyproject."""

    if not PYPROJECT_PATH.is_file():
        raise FileNotFoundError("pyproject.toml not found; verify repository path")
    with PYPROJECT_PATH.open("rb") as fh:
        data = tomllib.load(fh)
    extras = data.get("project", {}).get("optional-dependencies", {})
    reqs: dict[str, str] = {}
    for extra in extras_to_check:
        for spec in extras.get(extra, []):
            req = Requirement(spec)
            ver = next(
                (s.version for s in req.specifier if s.operator in (">=", "==")),
                None,
            )
            if ver:
                reqs[req.name] = ver
    return reqs


EXTRA_REQUIREMENTS = load_extra_requirements(extras_to_check())
REQUIREMENTS = {**BASE_REQUIREMENTS, **EXTRA_REQUIREMENTS}


# Packages lacking metadata in minimal environments.
# They are optional and may be intentionally absent.
SILENT_METADATA_PKGS = {
    "gitpython",
    "cibuildwheel",
    "duckdb-extension-vss",
    "spacy",
}


def _silenced_metadata(pkg: str) -> bool:
    """Return True if metadata warnings for ``pkg`` should be suppressed."""

    return pkg.lower() in SILENT_METADATA_PKGS or pkg.lower().startswith("types-")


@dataclass
class CheckResult:
    name: str
    current: str
    required: str

    def ok(self) -> bool:
        return Version(self.current) >= Version(self.required)


class VersionError(RuntimeError):
    """Raised when a requirement is not satisfied."""


def check_python() -> CheckResult:
    current = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    return CheckResult("Python", current, REQUIREMENTS["python"])


def check_task() -> CheckResult | None:
    required = REQUIREMENTS["task"]
    try:
        proc = subprocess.run(
            ["task", "--version"],
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError:
        logger.info(
            "Go Task %s+ not found; install it from https://taskfile.dev/ or run scripts/bootstrap.sh",
            required,
        )
        return None
    if proc.returncode != 0:
        hint = (
            f"Go Task {required}+ is required. Install it from https://taskfile.dev/ "
            "or run scripts/bootstrap.sh"
        )
        raise VersionError(hint)
    match = re.search(r"(\d+\.\d+\.\d+)", proc.stdout)
    if not match:
        raise VersionError("Could not determine Go Task version")
    current = match.group(1)
    if Version(current) < Version(required):
        hint = (
            f"Go Task {current} found, but {required}+ is required. Install it from "
            "https://taskfile.dev/ or run scripts/bootstrap.sh"
        )
        raise VersionError(hint)
    return CheckResult("Go Task", current, required)


def check_uv() -> CheckResult:
    try:
        proc = subprocess.run(["uv", "--version"], capture_output=True, text=True, check=False)
    except FileNotFoundError as exc:
        hint = "uv is not installed. Install it from https://github.com/astral-sh/uv"
        raise VersionError(hint) from exc
    if proc.returncode != 0:
        raise VersionError("uv is not installed. Install it from https://github.com/astral-sh/uv")
    match = re.search(r"(\d+\.\d+\.\d+)", proc.stdout)
    if not match:
        raise VersionError("Could not determine uv version")
    current = match.group(1)
    return CheckResult("uv", current, REQUIREMENTS["uv"])


def check_package(pkg: str) -> CheckResult | None:
    """Return installed version for ``pkg`` or skip if metadata is missing."""

    try:
        current = metadata.version(pkg)
    except metadata.PackageNotFoundError:
        if _silenced_metadata(pkg):
            logger.info("No package metadata found for %s; skipping", pkg)
            return None
        warnings.warn(
            f"package metadata not found for {pkg}",
            UserWarning,
        )
        logger.warning("No package metadata found for %s; skipping", pkg)
        return None
    required = REQUIREMENTS[pkg]
    return CheckResult(pkg, current, required)


def check_pytest_bdd() -> CheckResult | None:
    """Return pytest-bdd version or skip if unavailable."""

    try:
        import pytest_bdd  # noqa: F401
    except ModuleNotFoundError:  # pragma: no cover - failure path
        warnings.warn(
            "pytest-bdd import failed; run 'task install'.",
            UserWarning,
        )
        return None
    try:
        current = metadata.version("pytest-bdd")
    except metadata.PackageNotFoundError:
        warnings.warn(
            "package metadata not found for pytest-bdd",
            UserWarning,
        )
        logger.warning("No package metadata found for pytest-bdd; skipping")
        return None
    required = REQUIREMENTS["pytest-bdd"]
    return CheckResult("pytest-bdd", current, required)


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate required tool versions")
    parser.parse_args()

    extras = ", ".join(extras_to_check())
    print(f"Verifying extras: {extras}")

    checks = [check_python, check_task, check_uv]

    for pkg in sorted(EXTRA_REQUIREMENTS):
        if pkg == "pytest-bdd":
            checks.append(check_pytest_bdd)
            continue
        checks.append(lambda pkg=pkg: check_package(pkg))

    errors: list[str] = []
    for check in checks:
        try:
            result = check()
            if result is None:
                continue
            if result.ok():
                print(f"{result.name} {result.current}")
            else:
                errors.append(f"{result.name} {result.current} < required {result.required}")
        except Exception as exc:  # pragma: no cover - failure paths
            errors.append(str(exc))

    if errors:
        for err in errors:
            print(f"ERROR: {err}", file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()

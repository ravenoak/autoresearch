#!/usr/bin/env python3
"""Check development tool versions.

Usage:
    uv run python scripts/check_env.py

Versions for optional extras are loaded from ``pyproject.toml``. Extra groups
can be specified via the ``EXTRAS`` environment variable. The script validates
Python compatibility, flags unknown extras, checks Go Task availability with
``task --version``, and reports missing packages for requested extras. LLM
packages are skipped unless ``EXTRAS`` contains ``llm``.
"""
from __future__ import annotations

import argparse
import logging
import os
import re
import subprocess
import sys
import tomllib
from dataclasses import dataclass
from importlib import metadata
from pathlib import Path
from typing import Callable

if not (3, 12) <= sys.version_info < (4, 0):
    raise SystemExit(
        f"Python 3.12+ and <4.0 required, found {sys.version_info.major}.{sys.version_info.minor}"
    )

try:  # pragma: no cover - packaging is required
    from packaging.version import Version
    from packaging.requirements import Requirement
    from packaging.specifiers import SpecifierSet
except ModuleNotFoundError as exc:  # pragma: no cover
    raise SystemExit("packaging library is required") from exc

BASE_REQUIREMENTS = {
    "python": ">=3.12,<4.0",
    "task": "3.0.0",
    "uv": "0.7.0",
}

# LLM dependencies are optional; include ``llm`` via ``EXTRAS`` to validate them.
BASE_EXTRAS = ["dev-minimal", "test"]

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def extras_to_check(available: dict[str, list[str]]) -> list[str]:
    """Return extras from ``EXTRAS`` env var after validating names."""

    env_extras = os.environ.get("EXTRAS", "").split()
    missing = [e for e in env_extras if e and e not in available]
    if missing:
        raise SystemExit(f"Unknown extras: {', '.join(sorted(missing))}")
    return sorted(set(BASE_EXTRAS + env_extras))


REPO_ROOT = Path(__file__).resolve().parents[1]  # repository root
PYPROJECT_PATH = REPO_ROOT / "pyproject.toml"


def load_extra_requirements() -> tuple[dict[str, str], list[str]]:
    """Return versions for packages from specified extras in pyproject."""

    if not PYPROJECT_PATH.is_file():
        raise FileNotFoundError("pyproject.toml not found; verify repository path")
    with PYPROJECT_PATH.open("rb") as fh:
        data = tomllib.load(fh)
    available = data.get("project", {}).get("optional-dependencies", {})
    extras = extras_to_check(available)
    reqs: dict[str, str] = {}
    for extra in extras:
        for spec in available.get(extra, []):
            req = Requirement(spec)
            ver = next(
                (s.version for s in req.specifier if s.operator in (">=", "==")),
                None,
            )
            if ver:
                reqs[req.name] = ver
    return reqs, extras


EXTRA_REQUIREMENTS, EXTRAS = load_extra_requirements()
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


def _env_metadata_key(pkg: str) -> str:
    """Return the environment variable key storing a package version."""

    sanitized = re.sub(r"[^A-Z0-9]+", "_", pkg.upper())
    return f"AUTORESEARCH_{sanitized}_VERSION"


def _metadata_from_env(pkg: str) -> str | None:
    """Return a version string from environment metadata if available."""

    key = _env_metadata_key(pkg)
    value = os.environ.get(key)
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


ENV_METADATA_PROVIDERS: tuple[Callable[[str], str | None], ...] = (_metadata_from_env,)


def _resolve_missing_metadata(pkg: str) -> str | None:
    """Return a provider supplied version for ``pkg`` when metadata is absent."""

    for provider in ENV_METADATA_PROVIDERS:
        try:
            version = provider(pkg)
        except Exception as exc:  # pragma: no cover - defensive
            logger.debug("Metadata provider failed for %s", pkg, exc_info=exc)
            continue
        if version:
            return str(version)
    return None


@dataclass
class CheckResult:
    name: str
    current: str
    required: str
    spec: SpecifierSet | None = None

    def ok(self) -> bool:
        if self.spec is not None:
            return Version(self.current) in self.spec
        return Version(self.current) >= Version(self.required)


class VersionError(RuntimeError):
    """Raised when a requirement is not satisfied."""


def check_python() -> CheckResult:
    current = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    spec = SpecifierSet(REQUIREMENTS["python"])
    return CheckResult("Python", current, REQUIREMENTS["python"], spec)


def check_task() -> CheckResult:
    required = REQUIREMENTS["task"]
    try:
        proc = subprocess.run(
            ["task", "--version"],
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError as exc:
        hint = (
            "Go Task {required}+ not found; install it with scripts/setup.sh or "
            "your package manager"
        ).format(required=required)
        raise VersionError(hint) from exc
    if proc.returncode != 0:
        hint = (
            "Go Task {required}+ is required. Install it with scripts/setup.sh or "
            "your package manager"
        ).format(required=required)
        raise VersionError(hint)
    match = re.search(r"(\d+\.\d+\.\d+)", proc.stdout)
    if not match:
        raise VersionError("Could not determine Go Task version")
    current = match.group(1)
    if Version(current) < Version(required):
        hint = (
            "Go Task {current} found, but {required}+ is required. Install it with "
            "scripts/setup.sh or your package manager"
        ).format(current=current, required=required)
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
        version = _resolve_missing_metadata(pkg)
        if version is not None:
            logger.info("Using environment metadata for %s: %s", pkg, version)
            return CheckResult(pkg, version, REQUIREMENTS[pkg])
        if _silenced_metadata(pkg):
            logger.info("No package metadata found for %s; skipping", pkg)
            return None
        raise VersionError(f"{pkg} not installed; run 'task install'") from None
    required = REQUIREMENTS[pkg]
    return CheckResult(pkg, current, required)


def check_pytest_bdd() -> CheckResult:
    """Return pytest-bdd version or raise if unavailable."""

    try:
        import pytest_bdd  # noqa: F401
    except ModuleNotFoundError:
        raise VersionError("pytest-bdd is required; run 'task install'") from None
    try:
        current = metadata.version("pytest-bdd")
    except metadata.PackageNotFoundError:
        raise VersionError("pytest-bdd metadata not found; run 'task install'") from None
    required = REQUIREMENTS["pytest-bdd"]
    return CheckResult("pytest-bdd", current, required)


def make_check(pkg: str) -> Callable[[], CheckResult | None]:
    """Return a callable that checks ``pkg`` when invoked."""

    return lambda: check_package(pkg)


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate required tool versions")
    parser.parse_args()

    extras = ", ".join(EXTRAS)
    print(f"Verifying extras: {extras}")

    checks: list[Callable[[], CheckResult | None]] = [check_python, check_task, check_uv]

    for pkg in sorted(EXTRA_REQUIREMENTS):
        if pkg == "pytest-bdd":
            checks.append(check_pytest_bdd)
            continue
        checks.append(make_check(pkg))

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

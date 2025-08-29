#!/usr/bin/env python3
"""Check development tool versions.

Usage:
    uv run python scripts/check_env.py

Versions for optional extras are loaded from ``pyproject.toml``.
"""
from __future__ import annotations

import argparse
import importlib
import re
import subprocess
import sys
import tomllib
from dataclasses import dataclass
from importlib import metadata

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

# Packages checked from optional extras in pyproject.toml
EXTRA_PACKAGES = {
    "flake8": "dev",
    "mypy": "dev",
    "pytest": "dev",
    "pydantic": "dev",
    "pytest-httpx": "test",
    "tomli-w": "dev-minimal",
    "redis": "dev-minimal",
    "pytest-bdd": "test",
    "freezegun": "test",
    "hypothesis": "test",
}


def load_extra_requirements() -> dict[str, str]:
    """Return versions for packages in EXTRA_PACKAGES from pyproject extras."""

    with open("pyproject.toml", "rb") as fh:
        data = tomllib.load(fh)
    extras = data.get("project", {}).get("optional-dependencies", {})
    reqs: dict[str, str] = {}
    for pkg, extra in EXTRA_PACKAGES.items():
        for spec in extras.get(extra, []):
            req = Requirement(spec)
            if req.name == pkg:
                ver = next(
                    (s.version for s in req.specifier if s.operator in (">=", "==")),
                    None,
                )
                if ver:
                    reqs[pkg] = ver
                break
    return reqs


REQUIREMENTS = {**BASE_REQUIREMENTS, **load_extra_requirements()}


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
            f"Go Task {required}+ is required. Install it from https://taskfile.dev/ "
            "or run scripts/setup.sh"
        )
        raise VersionError(hint) from exc
    if proc.returncode != 0:
        hint = (
            f"Go Task {required}+ is required. Install it from https://taskfile.dev/ "
            "or run scripts/setup.sh"
        )
        raise VersionError(hint)
    match = re.search(r"(\d+\.\d+\.\d+)", proc.stdout)
    if not match:
        raise VersionError("Could not determine Go Task version")
    current = match.group(1)
    if Version(current) < Version(required):
        hint = (
            f"Go Task {current} found, but {required}+ is required. Install it from "
            "https://taskfile.dev/ or run scripts/setup.sh"
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


def check_module(module: str, package: str | None = None) -> CheckResult:
    importlib.import_module(module)
    pkg = package or module
    current = metadata.version(pkg)
    required = REQUIREMENTS[pkg]
    return CheckResult(pkg, current, required)


MODULE_MAP = {
    "flake8": "flake8",
    "mypy": "mypy",
    "pytest": "pytest",
    "pydantic": "pydantic",
    "pytest-httpx": "pytest_httpx",
    "tomli-w": "tomli_w",
    "redis": "redis",
    "pytest-bdd": "pytest_bdd",
    "freezegun": "freezegun",
    "hypothesis": "hypothesis",
}


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate required tool versions")
    parser.parse_args()

    extras = ", ".join(sorted(set(EXTRA_PACKAGES.values())))
    print(f"Verifying extras: {extras}")

    checks = [check_python, check_task, check_uv]

    for pkg, module in MODULE_MAP.items():
        checks.append(lambda module=module, pkg=pkg: check_module(module, pkg))

    errors: list[str] = []
    for check in checks:
        try:
            result = check()
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

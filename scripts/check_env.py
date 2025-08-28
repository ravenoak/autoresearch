#!/usr/bin/env python3
"""Check development tool versions.

Usage:
    uv run python scripts/check_env.py
"""
from __future__ import annotations

import argparse
import importlib
import re
import subprocess
import sys
from dataclasses import dataclass
from importlib import metadata

if sys.version_info < (3, 12):
    raise SystemExit(
        f"Python 3.12+ required, found {sys.version_info.major}.{sys.version_info.minor}"
    )

try:  # pragma: no cover - packaging is required
    from packaging.version import Version
except ModuleNotFoundError as exc:  # pragma: no cover
    raise SystemExit("packaging library is required") from exc

REQUIREMENTS = {
    "python": "3.12.0",
    "task": "3.0.0",
    "uv": "0.7.0",
    "flake8": "7.2.0",
    "mypy": "1.10.0",
    "pytest": "8.3.5",
    "pydantic": "2.0.0",
    "pytest-httpx": "0.35.0",
    "tomli-w": "1.2.0",
    "redis": "6.2.0",
    "pytest-bdd": "8.1.0",
    "freezegun": "1.5.5",
    "hypothesis": "6.138.3",
}


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


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate required tool versions")
    parser.parse_args()

    checks = [check_python, check_task]

    checks += [
        check_uv,
        lambda: check_module("flake8"),
        lambda: check_module("mypy"),
        lambda: check_module("pytest"),
        lambda: check_module("pytest_bdd", "pytest-bdd"),
        lambda: check_module("freezegun"),
        lambda: check_module("hypothesis"),
        lambda: check_module("pydantic"),
        lambda: check_module("pytest_httpx", "pytest-httpx"),
        lambda: check_module("tomli_w", "tomli-w"),
        lambda: check_module("redis"),
    ]

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

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
    "flake8": "7.2.0",
    "mypy": "1.10.0",
    "pytest": "8.3.5",
    "pytest-bdd": "8.1.0",
    "pydantic": "2.0.0",
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
    proc = subprocess.run(
        ["task", "--version"],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        raise VersionError("Go Task is not installed")
    match = re.search(r"(\d+\.\d+\.\d+)", proc.stdout)
    if not match:
        raise VersionError("Could not determine Go Task version")
    current = match.group(1)
    return CheckResult("Go Task", current, REQUIREMENTS["task"])


def check_module(module: str, package: str | None = None) -> CheckResult:
    importlib.import_module(module)
    pkg = package or module
    current = metadata.version(pkg)
    required = REQUIREMENTS[pkg]
    return CheckResult(pkg, current, required)


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate required tool versions")
    parser.parse_args()

    checks = [
        check_python,
        check_task,
        lambda: check_module("flake8"),
        lambda: check_module("mypy"),
        lambda: check_module("pytest"),
        lambda: check_module("pytest_bdd", "pytest-bdd"),
        lambda: check_module("pydantic"),
    ]

    errors: list[str] = []
    for check in checks:
        try:
            result = check()
            if result.ok():
                print(f"{result.name} {result.current}")
            else:
                errors.append(
                    f"{result.name} {result.current} < required {result.required}"
                )
        except Exception as exc:  # pragma: no cover - failure paths
            errors.append(str(exc))

    if errors:
        for err in errors:
            print(f"ERROR: {err}", file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()

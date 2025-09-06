#!/usr/bin/env python
"""Validate deployment environment and configuration.

Usage:
    uv run scripts/validate_deploy.py

This script verifies that required environment variables, optional extras, and
configuration files exist before deployment. It also checks for a specified
container engine so misconfigurations fail fast.
"""
from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path
from typing import Any, Mapping, Sequence

import tomllib
import yaml
from jsonschema import Draft7Validator

REQUIRED_ENV_VARS = ("DEPLOY_ENV", "CONFIG_DIR")
REQUIRED_FILES = ("deploy.yml", ".env")

DEPLOY_SCHEMA = {
    "type": "object",
    "properties": {
        "version": {"type": ["integer", "string"]},
        "services": {
            "type": "array",
            "items": {"type": "string"},
        },
    },
    "required": ["version"],
}

ENV_SCHEMA = {
    "type": "object",
    "properties": {"KEY": {"type": "string", "minLength": 1}},
    "required": ["KEY"],
}


def _load_valid_extras() -> set[str]:
    """Return optional dependency groups from ``pyproject.toml``."""

    project_root = Path(__file__).resolve().parents[1]
    pyproject = project_root / "pyproject.toml"
    if not pyproject.is_file():
        return set()
    with pyproject.open("rb") as fh:
        data = tomllib.load(fh)
    extras = data.get("project", {}).get("optional-dependencies", {})
    return set(extras)


VALID_EXTRAS = _load_valid_extras()


def _missing_env() -> list[str]:
    """Return missing required environment variables."""
    return [name for name in REQUIRED_ENV_VARS if not os.getenv(name)]


def _missing_files(config_dir: Path) -> list[Path]:
    """Return missing configuration files in ``config_dir``."""
    return [config_dir / name for name in REQUIRED_FILES if not (config_dir / name).is_file()]


def _load_yaml(path: Path) -> Mapping[str, Any]:
    """Load YAML data from ``path``."""
    with path.open() as fh:
        return yaml.safe_load(fh) or {}


def _load_env_file(path: Path) -> Mapping[str, str]:
    """Parse simple ``.env`` files into a mapping."""
    data: dict[str, str] = {}
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        data[key.strip()] = value.strip()
    return data


def _unknown_extras(value: str) -> list[str]:
    """Return extras not defined in ``pyproject.toml``."""

    return [extra for extra in value.split() if extra and extra not in VALID_EXTRAS]


def _check_container_engine() -> str | None:
    """Return an error message if the container engine is missing."""

    engine = os.getenv("CONTAINER_ENGINE")
    if not engine:
        return None
    if shutil.which(engine) is None:
        return f"Container engine '{engine}' not found"
    return None


def _schema_errors(data: Mapping[str, Any], schema: Mapping[str, Any]) -> list[str]:
    """Return validation errors for ``data`` against ``schema``."""
    validator = Draft7Validator(schema)
    return [error.message for error in validator.iter_errors(data)]


def main(argv: Sequence[str] | None = None) -> int:
    missing_env = _missing_env()
    if missing_env:
        print(
            f"Missing environment variables: {', '.join(missing_env)}",
            file=sys.stderr,
        )
        return 1
    extras_err = _unknown_extras(os.getenv("EXTRAS", ""))
    if extras_err:
        print(f"Unknown extras: {', '.join(extras_err)}", file=sys.stderr)
        return 1
    engine_err = _check_container_engine()
    if engine_err:
        print(engine_err, file=sys.stderr)
        return 1
    config_dir = Path(os.environ["CONFIG_DIR"])
    if not config_dir.is_dir():
        print(f"CONFIG_DIR not found: {config_dir}", file=sys.stderr)
        return 1

    missing_files = _missing_files(config_dir)
    if missing_files:
        missing = ", ".join(str(p) for p in missing_files)
        print(f"Missing configuration files: {missing}", file=sys.stderr)
        return 1
    yaml_data = _load_yaml(config_dir / "deploy.yml")
    yaml_errors = _schema_errors(yaml_data, DEPLOY_SCHEMA)
    if yaml_errors:
        errors = "; ".join(yaml_errors)
        print(f"Schema errors in deploy.yml: {errors}", file=sys.stderr)
        return 1
    env_data = _load_env_file(config_dir / ".env")
    env_errors = _schema_errors(env_data, ENV_SCHEMA)
    if env_errors:
        errors = "; ".join(env_errors)
        print(f"Schema errors in .env: {errors}", file=sys.stderr)
        return 1
    print("Deployment configuration validated.")
    return 0


if __name__ == "__main__":  # pragma: no cover - manual invocation
    raise SystemExit(main())

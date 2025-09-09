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
VALID_DEPLOY_ENVS = {
    "production",
    "staging",
    "development",
    "linux",
    "macos",
    "windows",
}
VALID_ENGINES = {"docker", "podman"}

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

DEFAULT_DEPLOY_DIR = Path(__file__).resolve().parent / "deploy"


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
    """Load YAML data from ``path``.

    Raises ``ValueError`` if the file contains invalid YAML.
    """

    try:
        with path.open() as fh:
            return yaml.safe_load(fh) or {}
    except yaml.YAMLError as exc:  # pragma: no cover - parse error path
        raise ValueError(f"Invalid YAML in {path}: {exc}") from exc


def _load_env_file(path: Path) -> Mapping[str, str]:
    """Parse simple ``.env`` files into a mapping.

    Raises ``ValueError`` if a key is defined more than once.
    """

    data: dict[str, str] = {}
    for idx, line in enumerate(path.read_text().splitlines(), start=1):
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        if key in data:
            raise ValueError(f"Duplicate key '{key}' in {path} line {idx}")
        data[key] = value.strip()
    return data


def _unknown_extras(value: str) -> list[str]:
    """Return extras not defined in ``pyproject.toml``."""

    return [extra for extra in value.split() if extra and extra not in VALID_EXTRAS]


def _check_container_engine() -> str | None:
    """Return an error message if the container engine is missing."""

    engine = os.getenv("CONTAINER_ENGINE")
    if not engine:
        return None
    if engine not in VALID_ENGINES:
        return f"Unsupported container engine '{engine}'"
    if shutil.which(engine) is None:
        return f"Container engine '{engine}' not found"
    return None


def _schema_errors(data: Mapping[str, Any], schema: Mapping[str, Any]) -> list[str]:
    """Return validation errors for ``data`` against ``schema``."""
    validator = Draft7Validator(schema)
    return [error.message for error in validator.iter_errors(data)]


def _validate_deploy_dir(deploy_dir: Path) -> list[str]:
    """Validate .env and YAML config files under ``deploy_dir``.

    Returns a list of error messages for any invalid files.
    """

    errors: list[str] = []
    if not deploy_dir.is_dir():
        return [f"Deployment directory not found: {deploy_dir}"]
    for env_file in deploy_dir.rglob("*.env"):
        try:
            env_data = _load_env_file(env_file)
        except ValueError as exc:
            errors.append(str(exc))
            continue
        env_errors = _schema_errors(env_data, ENV_SCHEMA)
        if env_errors:
            msg = "; ".join(env_errors)
            errors.append(f"Schema errors in {env_file}: {msg}")
    for yaml_file in list(deploy_dir.rglob("*.yml")) + list(deploy_dir.rglob("*.yaml")):
        try:
            yaml_data = _load_yaml(yaml_file)
        except ValueError as exc:
            errors.append(str(exc))
            continue
        yaml_errors = _schema_errors(yaml_data, DEPLOY_SCHEMA)
        if yaml_errors:
            msg = "; ".join(yaml_errors)
            errors.append(f"Schema errors in {yaml_file}: {msg}")
    return errors


def _preflight(env: Mapping[str, str]) -> tuple[Path | None, list[str]]:
    """Check environment variables and configuration files.

    Returns ``(config_dir, errors)`` where ``config_dir`` is the resolved
    directory or ``None`` if unavailable. ``errors`` contains human-readable
    messages for any problems.
    """

    errors: list[str] = []
    missing_env = [name for name in REQUIRED_ENV_VARS if not env.get(name)]
    if missing_env:
        errors.append(f"Missing environment variables: {', '.join(missing_env)}")
        return None, errors
    if env["DEPLOY_ENV"] not in VALID_DEPLOY_ENVS:
        allowed = ", ".join(sorted(VALID_DEPLOY_ENVS))
        errors.append(f"DEPLOY_ENV must be one of {allowed}")
        return None, errors
    config_dir = Path(env["CONFIG_DIR"])
    if not config_dir.is_dir():
        errors.append(f"CONFIG_DIR not found: {config_dir}")
        return None, errors
    missing_files = _missing_files(config_dir)
    if missing_files:
        missing = ", ".join(str(p) for p in missing_files)
        errors.append(f"Missing configuration files: {missing}")
    return config_dir, errors


def load_config(config_dir: Path) -> tuple[Mapping[str, Any], Mapping[str, str]]:
    """Return ``deploy.yml`` and ``.env`` data from ``config_dir``.

    Raises ``ValueError`` if either file contains invalid syntax. The caller
    is responsible for handling schema validation.
    """

    yaml_data = _load_yaml(config_dir / "deploy.yml")
    env_data = _load_env_file(config_dir / ".env")
    return yaml_data, env_data


def main(argv: Sequence[str] | None = None) -> int:
    config_dir, errors = _preflight(os.environ)
    if errors:
        print("; ".join(errors), file=sys.stderr)
        return 1
    assert config_dir is not None
    extras_err = _unknown_extras(os.getenv("EXTRAS", ""))
    if extras_err:
        print(f"Unknown extras: {', '.join(extras_err)}", file=sys.stderr)
        return 1
    engine_err = _check_container_engine()
    if engine_err:
        print(engine_err, file=sys.stderr)
        return 1
    try:
        yaml_data, env_data = load_config(config_dir)
    except ValueError as exc:
        print(exc, file=sys.stderr)
        return 1
    yaml_errors = _schema_errors(yaml_data, DEPLOY_SCHEMA)
    if yaml_errors:
        msg = "; ".join(yaml_errors)
        print(f"Schema errors in deploy.yml: {msg}", file=sys.stderr)
        return 1
    env_errors = _schema_errors(env_data, ENV_SCHEMA)
    if env_errors:
        msg = "; ".join(env_errors)
        print(f"Schema errors in .env: {msg}", file=sys.stderr)
        return 1
    deploy_dir = Path(os.getenv("DEPLOY_DIR", DEFAULT_DEPLOY_DIR))
    dir_errors = _validate_deploy_dir(deploy_dir)
    if dir_errors:
        print("; ".join(dir_errors), file=sys.stderr)
        return 1

    print("Deployment configuration validated.")
    return 0


if __name__ == "__main__":  # pragma: no cover - manual invocation
    raise SystemExit(main())

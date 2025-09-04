#!/usr/bin/env python
"""Validate deployment environment and configuration.

Usage:
    uv run scripts/validate_deploy.py

This script verifies that required environment variables and configuration
files exist before deployment.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any, Mapping, Sequence

import yaml

REQUIRED_ENV_VARS = ("DEPLOY_ENV", "CONFIG_DIR")
REQUIRED_FILES = ("deploy.yml", ".env")
REQUIRED_YAML_KEYS = ("version",)
REQUIRED_ENV_FILE_KEYS = ("KEY",)


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


def _missing_keys(data: Mapping[str, Any], required: Sequence[str]) -> list[str]:
    """Return missing keys from ``data``."""
    return [key for key in required if key not in data]


def main(argv: Sequence[str] | None = None) -> int:
    missing_env = _missing_env()
    if missing_env:
        print(
            f"Missing environment variables: {', '.join(missing_env)}",
            file=sys.stderr,
        )
        return 1
    config_dir = Path(os.environ["CONFIG_DIR"])
    missing_files = _missing_files(config_dir)
    if missing_files:
        missing = ", ".join(str(p) for p in missing_files)
        print(f"Missing configuration files: {missing}", file=sys.stderr)
        return 1
    yaml_data = _load_yaml(config_dir / "deploy.yml")
    missing_yaml = _missing_keys(yaml_data, REQUIRED_YAML_KEYS)
    if missing_yaml:
        missing = ", ".join(missing_yaml)
        print(f"Missing keys in deploy.yml: {missing}", file=sys.stderr)
        return 1
    env_data = _load_env_file(config_dir / ".env")
    missing_env_file = _missing_keys(env_data, REQUIRED_ENV_FILE_KEYS)
    if missing_env_file:
        missing = ", ".join(missing_env_file)
        print(f"Missing keys in .env: {missing}", file=sys.stderr)
        return 1
    print("Deployment configuration validated.")
    return 0


if __name__ == "__main__":  # pragma: no cover - manual invocation
    raise SystemExit(main())

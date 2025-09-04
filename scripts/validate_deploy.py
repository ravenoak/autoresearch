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
from typing import Sequence

REQUIRED_ENV_VARS = ("DEPLOY_ENV", "CONFIG_DIR")
REQUIRED_FILES = ("deploy.yml", ".env")


def _missing_env() -> list[str]:
    """Return missing required environment variables."""
    return [name for name in REQUIRED_ENV_VARS if not os.getenv(name)]


def _missing_files(config_dir: Path) -> list[Path]:
    """Return missing configuration files in ``config_dir``."""
    return [config_dir / name for name in REQUIRED_FILES if not (config_dir / name).is_file()]


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
    print("Deployment configuration validated.")
    return 0


if __name__ == "__main__":  # pragma: no cover - manual invocation
    raise SystemExit(main())

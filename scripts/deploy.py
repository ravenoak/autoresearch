#!/usr/bin/env python
"""Simple deployment helper.

This script validates configuration and performs a basic health check of a running
Autoresearch server. It should be executed after starting the service to ensure
all environment variables are loaded correctly and the API is responsive.
"""
from __future__ import annotations

import os
import sys
from typing import Sequence

import httpx
from dotenv import load_dotenv

from autoresearch.config.loader import get_config
from autoresearch.errors import ConfigError


def validate_config() -> None:
    """Load and validate the Autoresearch configuration."""
    load_dotenv()
    try:
        get_config()
    except ConfigError as exc:
        print(f"Configuration error: {exc}")
        sys.exit(1)
    print("Configuration valid")


def health_check(url: str = "http://localhost:8000/metrics") -> None:
    """Check that the API responds successfully."""
    try:
        response = httpx.get(url, timeout=5)
    except Exception as exc:  # pragma: no cover - runtime check
        print(f"Health check failed: {exc}")
        sys.exit(1)
    if response.status_code != 200:
        print(f"Health check failed: status {response.status_code}")
        sys.exit(1)
    print("Health check passed")


def main(argv: Sequence[str] | None = None) -> int:
    validate_config()
    health_check()
    return 0


if __name__ == "__main__":  # pragma: no cover - manual invocation
    raise SystemExit(main())

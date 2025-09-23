#!/usr/bin/env python
"""Simple deployment helper.

Usage:
    uv run python scripts/deploy.py

This script validates configuration and performs a basic health check of a
running Autoresearch server. It should be executed after starting the service
to ensure all required settings exist and the API is responsive. Set
``AUTORESEARCH_HEALTHCHECK_URL`` to override the health endpoint or leave it
empty to skip the check.
"""
from __future__ import annotations

import os
import sys
from typing import Sequence

import httpx
from dotenv import load_dotenv

from autoresearch.config.loader import ConfigLoader
from autoresearch.errors import ConfigError


CONFIG_FILE_ENV = "AUTORESEARCH_CONFIG_FILE"

REQUIRED_ENV = {
    "SERPER_API_KEY": lambda cfg: "serper" in cfg.search.backends,
    "BRAVE_SEARCH_API_KEY": lambda cfg: "brave" in cfg.search.backends,
    "OPENAI_API_KEY": lambda cfg: "openai" in cfg.llm_backend.lower(),
    "OPENROUTER_API_KEY": lambda cfg: "openrouter" in cfg.llm_backend.lower(),
}


def _ensure_config_file() -> str:
    """Return path to configuration file, exiting if it does not exist."""
    path = os.getenv(CONFIG_FILE_ENV, "autoresearch.toml")
    if not os.path.exists(path):
        print(f"Configuration file '{path}' not found")
        sys.exit(1)
    return path


def _check_required_settings(config_path: str) -> list[str]:
    """Return missing environment variables based on the active config."""
    loader = ConfigLoader(search_paths=[config_path])
    profile = os.getenv("AUTORESEARCH_ACTIVE_PROFILE")
    if profile:
        loader.set_active_profile(profile)
    cfg = loader.config
    missing: list[str] = []
    for name, predicate in REQUIRED_ENV.items():
        if predicate(cfg) and not os.getenv(name):
            missing.append(name)
    return missing


def validate_config() -> None:
    """Load configuration and ensure required settings exist.

    Only load environment variables from a local .env file in the current
    working directory to avoid leaking parent repo settings into validation
    runs (e.g., during tests).
    """
    local_env = os.path.join(os.getcwd(), ".env")
    load_dotenv(dotenv_path=local_env)
    cfg_path = _ensure_config_file()
    try:
        _missing = _check_required_settings(cfg_path)
    except ConfigError as exc:
        print(f"Configuration error: {exc}")
        sys.exit(1)
    if _missing:
        print("Missing required settings: " + ", ".join(_missing))
        sys.exit(1)
    print("Configuration valid")


def health_check(url: str | None = None) -> None:
    """Check that the API responds successfully."""
    url = url or os.getenv("AUTORESEARCH_HEALTHCHECK_URL", "http://localhost:8000/metrics")
    if not url:
        print("Health check skipped")
        return
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

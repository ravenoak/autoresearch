#!/usr/bin/env bash
# Usage: bash scripts/deploy/macos.sh
# Validate configuration and deploy on macOS.
set -euo pipefail

uv run scripts/validate_deploy.py
uv run python scripts/deploy.py

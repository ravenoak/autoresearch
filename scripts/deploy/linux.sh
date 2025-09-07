#!/usr/bin/env bash
# Usage: bash scripts/deploy/linux.sh
# Validate configuration and deploy on Linux.
set -euo pipefail

uv run scripts/validate_deploy.py
uv run python scripts/deploy.py

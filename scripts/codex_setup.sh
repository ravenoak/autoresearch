#!/usr/bin/env bash
set -euo pipefail

# Ensure Python 3.12 is available before proceeding
if ! command -v python3.12 >/dev/null 2>&1; then
    echo "python3.12 is required but was not found in PATH" >&2
    exit 1
fi

echo "Setting up Codex environment..."

export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get install -y \
        build-essential python3-dev python3-venv cmake pkg-config git libssl-dev libffi-dev libxml2-dev libargon2-dev libblas-dev liblapack-dev libopenblas-dev liblmdb-dev libz3-dev libcurl4-openssl-dev
apt-get clean
rm -rf /var/lib/apt/lists/*

# Install Go Task for running Taskfile commands if not already installed
if ! command -v task >/dev/null 2>&1; then
    curl -sL https://taskfile.dev/install.sh | sh -s -- -b /usr/local/bin
fi

# Verify Go Task was installed
if [ ! -x /usr/local/bin/task ]; then
    echo "Go Task not found at /usr/local/bin/task." >&2
    echo "Re-run: curl -sL https://taskfile.dev/install.sh | sh -s -- -b /usr/local/bin" >&2
    exit 1
fi

# Run the main setup script to install all extras needed for testing
./scripts/setup.sh full,dev,test

# Pre-download models so tests can run without network access
uv run python - <<'PY'
from sentence_transformers import SentenceTransformer
SentenceTransformer("all-MiniLM-L6-v2")
PY

uv run python -m spacy download en_core_web_sm

# Pre-load ontology reasoner so tests can run offline
uv run python - <<'PY'
import owlrl  # noqa: F401
PY

# Cache DuckDB extensions for offline use (vss by default)
uv run python scripts/download_duckdb_extensions.py --output-dir ./extensions

# All Python setup is handled by setup.sh using uv pip


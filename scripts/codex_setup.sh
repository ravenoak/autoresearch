#!/usr/bin/env bash
set -euo pipefail

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

# Run the main setup script to install dev dependencies and extras with uv
./scripts/setup.sh
# All Python setup is handled by setup.sh using uv pip


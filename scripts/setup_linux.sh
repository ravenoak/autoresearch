#!/usr/bin/env bash
# Usage: AR_EXTRAS="nlp ui" ./scripts/setup_linux.sh
# Linux-specific environment setup; installs OS packages when possible.
# The universal setup is invoked by setup.sh after this script completes.
set -euo pipefail

if [[ "$(uname -s)" != "Linux" ]]; then
    echo "This script is intended for Linux hosts." >&2
    exit 1
fi

SCRIPT_DIR="$(dirname "$0")"
source "$SCRIPT_DIR/setup_common.sh"

if command -v apt-get >/dev/null 2>&1; then
    if [[ "$(id -u)" -ne 0 ]]; then
        echo "Skipping system package installation; run as root if required." >&2
    else
        export DEBIAN_FRONTEND=noninteractive
        retry 3 apt-get update
        retry 3 apt-get install -y \
            build-essential python3-dev python3-venv cmake pkg-config git \
            libssl-dev libffi-dev libxml2-dev libargon2-dev libblas-dev \
            liblapack-dev libopenblas-dev liblmdb-dev libz3-dev \
            libcurl4-openssl-dev
        retry 3 apt-get clean
        rm -rf /var/lib/apt/lists/*
    fi
else
    echo "apt-get not found; please install required packages manually." >&2
fi


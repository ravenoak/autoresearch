#!/usr/bin/env bash
# Usage: AR_EXTRAS="nlp ui" ./scripts/setup_macos.sh
# macOS-specific environment setup; installs dependencies via Homebrew.
# Requires Python 3.12+ and uv>=0.7.0 (enforced by setup_common.sh).
# The universal setup is invoked by setup.sh after this script completes.
set -euo pipefail

if [[ "$(uname -s)" != "Darwin" ]]; then
    echo "This script is intended for macOS hosts." >&2
    exit 1
fi

SCRIPT_DIR="$(dirname "$0")"
source "$SCRIPT_DIR/setup_common.sh"

if command -v brew >/dev/null 2>&1; then
    brew update
    brew install python cmake pkg-config git libffi libxml2 z3
else
    echo "Homebrew is required to install dependencies. Install from https://brew.sh/" >&2
fi

# Ensure the virtual environment's bin directory is available to later steps.
ensure_venv_bin_on_path "$(pwd)/.venv/bin"


#!/usr/bin/env bash
# Usage: source scripts/setup_common.sh
# Shared helpers for environment setup scripts.
set -euo pipefail

install_dev_test_extras() {
    echo "Installing dev and test extras via uv sync --extra dev --extra test"
    uv sync --extra dev --extra test
    uv pip install -e .
}

ensure_venv_bin_on_path() {
    local venv_bin="${1:-.venv/bin}"
    case ":$PATH:" in
        *":$venv_bin:"*) ;;
        *) export PATH="$venv_bin:$PATH" ;;
    esac
}

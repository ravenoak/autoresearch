#!/usr/bin/env bash
# Usage: source scripts/setup_common.sh
# Shared helpers for environment setup scripts.
set -euo pipefail

install_dev_test_extras() {
    local extras="dev test"
    if [ -n "${AR_EXTRAS:-}" ]; then
        extras="$extras ${AR_EXTRAS}"
    fi
    echo "Installing extras via uv sync --extra ${extras// / --extra }"
    uv sync $(for e in $extras; do printf -- '--extra %s ' "$e"; done)
    uv pip install -e .
}

ensure_venv_bin_on_path() {
    local venv_bin="${1:-.venv/bin}"
    case ":$PATH:" in
        *":$venv_bin:"*) ;;
        *) export PATH="$venv_bin:$PATH" ;;
    esac
}

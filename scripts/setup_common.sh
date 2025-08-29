#!/usr/bin/env bash
# Usage: source scripts/setup_common.sh
# Shared helpers for environment setup scripts.
set -euo pipefail

retry() {
    local -r max_attempts="$1"; shift
    local attempt=1
    until "$@"; do
        if (( attempt == max_attempts )); then
            echo "Command failed after $attempt attempts: $*" >&2
            return 1
        fi
        echo "Attempt $attempt failed: $*. Retrying..." >&2
        attempt=$((attempt + 1))
        sleep 2
    done
}

ensure_uv() {
    if ! command -v uv >/dev/null 2>&1; then
        curl -LsSf https://astral.sh/uv/install.sh | sh -s -- --quiet
        export PATH="$HOME/.local/bin:$PATH"
    fi
    command -v uv >/dev/null 2>&1 \
        || { echo "uv is required but missing" >&2; return 1; }
}

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

record_vector_extension_path() {
    local path="$1"
    for env_file in .env .env.offline; do
        if [ ! -f "$env_file" ]; then
            echo "VECTOR_EXTENSION_PATH=$path" >"$env_file"
        elif grep -q "VECTOR_EXTENSION_PATH" "$env_file"; then
            sed -i.bak \
                "s|VECTOR_EXTENSION_PATH=.*|VECTOR_EXTENSION_PATH=$path|" \
                "$env_file" && rm -f "$env_file.bak"
        else
            echo "VECTOR_EXTENSION_PATH=$path" >>"$env_file"
        fi
    done
}

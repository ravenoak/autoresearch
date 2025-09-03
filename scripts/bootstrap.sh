#!/usr/bin/env bash
# Usage: ./scripts/bootstrap.sh
# Ensure Go Task is installed in .venv/bin.
set -euo pipefail

SCRIPT_DIR="$(dirname "$0")"
source "$SCRIPT_DIR/setup_common.sh"

VENV_BIN="$(pwd)/.venv/bin"
TASK_BIN="$VENV_BIN/task"

ensure_uv
uv venv
ensure_venv_bin_on_path "$VENV_BIN"

if [ ! -x "$TASK_BIN" ]; then
    echo "Go Task not found; installing into $VENV_BIN..."
    if command -v task >/dev/null 2>&1; then
        ln -sf "$(command -v task)" "$TASK_BIN"
    else
        curl -sSL https://taskfile.dev/install.sh | sh -s -- -b "$VENV_BIN" || {
            echo "Failed to install Go Task. See docs/installation.md for manual steps." >&2
            exit 1
        }
    fi
fi

"$TASK_BIN" --version

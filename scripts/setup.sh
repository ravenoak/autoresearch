#!/usr/bin/env bash
# Usage: ./scripts/setup.sh
# Set AR_SKIP_GPU=0 to include GPU-only dependencies.
# Detects the host platform, ensures uv and Go Task are installed, and installs
# all extras required for unit, integration, and behavior tests.
set -euo pipefail

SCRIPT_DIR="$(dirname "$0")"
source "$SCRIPT_DIR/setup_common.sh"

VENV_BIN="$(pwd)/.venv/bin"
TASK_BIN="$VENV_BIN/task"

install_go_task() {
    echo "Installing Go Task into $VENV_BIN..."
    ensure_uv
    uv venv
    mkdir -p "$VENV_BIN"
    curl -sSL https://taskfile.dev/install.sh | sh -s -- -b "$VENV_BIN" || {
        echo "Warning: failed to download Go Task; install manually from" \
            " https://taskfile.dev/installation/ and re-run setup" >&2
        return
    }
}

if [ ! -x "$TASK_BIN" ]; then
    install_go_task
fi

ensure_venv_bin_on_path "$VENV_BIN"
export PATH="$VENV_BIN:$PATH"

case "$(uname -s)" in
Linux*)
    "$SCRIPT_DIR/setup_linux.sh" "$@"
    ;;
Darwin*)
    "$SCRIPT_DIR/setup_macos.sh" "$@"
    ;;
*)
    echo "Unsupported platform; skipping platform-specific setup." >&2
    ;;
esac

install_test_extras() {
    # Install test dependencies when Go Task is unavailable so pytest can run.
    ensure_uv
    uv venv
    ensure_venv_bin_on_path "$(pwd)/.venv/bin"
    uv pip install -e ".[test]"
    mkdir -p extensions
    if uv run "$SCRIPT_DIR/download_duckdb_extensions.py" --output-dir ./extensions; then
        # Ignore stub files by selecting only non-empty extensions.
        VSS_EXTENSION=$(find ./extensions -name "vss*.duckdb_extension" -size +0c | head -n 1)
    else
        echo "Warning: duckdb extension download failed; falling back to stub" >&2
    fi
    VSS_EXTENSION="${VSS_EXTENSION:-./extensions/vss/vss.duckdb_extension}"
    if [ ! -f "$VSS_EXTENSION" ]; then
        mkdir -p "$(dirname "$VSS_EXTENSION")"
        : >"$VSS_EXTENSION"
    fi
    if [ ! -s "$VSS_EXTENSION" ]; then
        echo "Using stub VSS extension at $VSS_EXTENSION" >&2
    fi
    record_vector_extension_path "$VSS_EXTENSION"
}

if [ ! -x "$TASK_BIN" ]; then
    echo "Go Task not found; installing test extras..."
    install_test_extras
else
    AR_SKIP_SMOKE_TEST=1 \
        AR_EXTRAS="${AR_EXTRAS:-nlp ui vss parsers git distributed analysis}" \
        "$SCRIPT_DIR/setup_universal.sh" "$@" || {
        echo "setup_universal.sh failed; installing test extras without Go Task..."
        install_test_extras
    }
fi

# Run the smoke test even if the VSS extension is missing; the script
# handles the zero-byte stub and prints warnings when vector search is
# unavailable.
echo "Running smoke test to verify environment..."
if ! uv run python scripts/smoke_test.py; then
    echo "Smoke test failed; environment may be incomplete" >&2
fi

task --version || echo "task --version failed; continuing without Go Task" >&2

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
ensure_venv_bin_on_path "$VENV_BIN"
export PATH="$VENV_BIN:$PATH"

install_go_task() {
    echo "Installing Go Task into $VENV_BIN..."
    ensure_uv
    uv venv
    ensure_venv_bin_on_path "$VENV_BIN"
    if command -v task >/dev/null 2>&1; then
        ln -sf "$(command -v task)" "$TASK_BIN"
    else
        curl -sSL https://taskfile.dev/install.sh | sh -s -- -b "$VENV_BIN" || {
            echo "Warning: failed to download Go Task; install manually from" \
                " https://taskfile.dev/installation/ and re-run setup" >&2
            return
        }
    fi
}

if [ ! -x "$TASK_BIN" ]; then
    install_go_task
fi

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
    if ! uv run "$SCRIPT_DIR/download_duckdb_extensions.py" --output-dir ./extensions; then
        echo "Warning: duckdb extension download failed; using stub" >&2
    fi
    # Ignore stub files by selecting only non-empty extensions and create a
    # zero-byte placeholder when none are available. This allows offline setup
    # to proceed while still recording a valid path for DuckDB.
    VSS_EXTENSION=$(find ./extensions -name "vss*.duckdb_extension" \
        -size +0c | head -n 1)
    if [ -z "$VSS_EXTENSION" ]; then
        VSS_EXTENSION="./extensions/vss/vss.duckdb_extension"
        mkdir -p "$(dirname "$VSS_EXTENSION")"
        : >"$VSS_EXTENSION"
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

# Run the smoke test even when the VSS extension is missing. Ignore failures
# when only the zero-byte stub exists so offline setups do not halt.
VSS_EXTENSION=$(find ./extensions -name "vss*.duckdb_extension" -size +0c | head -n 1)
if [ -n "$VSS_EXTENSION" ]; then
    echo "Running smoke test to verify environment..."
    uv run python scripts/smoke_test.py || \
        echo "Smoke test failed; environment may be incomplete" >&2
else
    echo "VSS extension not found; running smoke test with stub..."
    uv run python scripts/smoke_test.py >/dev/null || true
fi

task --version || echo "task --version failed; continuing without Go Task" >&2

#!/usr/bin/env bash
# Usage: ./scripts/setup.sh
# Set AR_SKIP_GPU=0 to include GPU-only dependencies.
# Detects the host platform, ensures uv and Go Task are installed, and installs
# all extras required for unit, integration, and behavior tests.
set -euo pipefail

SCRIPT_DIR="$(dirname "$0")"
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
    source "$SCRIPT_DIR/setup_common.sh"
    ensure_uv
    uv venv
    ensure_venv_bin_on_path "$(pwd)/.venv/bin"
    uv pip install -e ".[test]"
    mkdir -p extensions
    if uv run "$SCRIPT_DIR/download_duckdb_extensions.py" --output-dir ./extensions; then
        VSS_EXTENSION=$(find ./extensions -name "vss*.duckdb_extension" | head -n 1)
    fi
    VSS_EXTENSION="${VSS_EXTENSION:-./extensions/vss/vss.duckdb_extension}"
    record_vector_extension_path "$VSS_EXTENSION"
}

if ! command -v task >/dev/null 2>&1; then
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

# Run smoke test only when a real extension is present
# Network failures produce a stub so the environment can still install.
VSS_EXTENSION=$(find ./extensions -name "vss*.duckdb_extension" | head -n 1)
if [ -n "$VSS_EXTENSION" ] && [ -s "$VSS_EXTENSION" ]; then
    echo "Running smoke test to verify environment..."
    uv run python scripts/smoke_test.py
else
    echo "Skipping smoke test; using offline stub."
fi

# Ensure Go Task resides in the virtual environment so subsequent Taskfile
# invocations use the expected binary. Link an existing installation when
# possible; otherwise download it.
VENV_BIN="$(pwd)/.venv/bin"
TASK_BIN="$VENV_BIN/task"
if [ ! -x "$TASK_BIN" ]; then
    echo "Installing Go Task into $VENV_BIN..."
    mkdir -p "$VENV_BIN"
    if command -v task >/dev/null 2>&1; then
        ln -sf "$(command -v task)" "$TASK_BIN"
    else
        curl -sSL https://taskfile.dev/install.sh | sh -s -- -b "$VENV_BIN" || true
    fi
fi
"$TASK_BIN" --version >/dev/null 2>&1 \
    || echo "task --version failed; continuing without Go Task" >&2


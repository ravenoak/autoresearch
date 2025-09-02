#!/usr/bin/env bash
# Usage: ./scripts/setup.sh
# Set AR_SKIP_GPU=0 to include GPU-only dependencies.
# Detects the host platform, ensures uv and Go Task are installed, and installs
# all extras required for unit, integration, and behavior tests.
set -euo pipefail

SCRIPT_DIR="$(dirname "$0")"
source "$SCRIPT_DIR/setup_common.sh"
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

# Run the smoke test even when the VSS extension is missing; a stub will be used.
VSS_EXTENSION=$(find ./extensions -name "vss*.duckdb_extension" -size +0c | head -n 1)
if [ -n "$VSS_EXTENSION" ]; then
    echo "Running smoke test to verify environment..."
else
    echo "VSS extension not found; running smoke test with stub..."
fi
uv run python scripts/smoke_test.py ||
    echo "Smoke test failed; environment may be incomplete" >&2

# Ensure Go Task resides in the virtual environment so subsequent Taskfile
# invocations use the expected binary. Link an existing installation when
# possible; otherwise download it.
VENV_BIN="$(pwd)/.venv/bin"
ensure_venv_bin_on_path "$VENV_BIN"
TASK_BIN="$VENV_BIN/task"
if [ ! -x "$TASK_BIN" ]; then
    echo "Installing Go Task into $VENV_BIN..."
    mkdir -p "$VENV_BIN"
    if command -v task >/dev/null 2>&1; then
        ln -sf "$(command -v task)" "$TASK_BIN"
    else
        curl -sSL https://taskfile.dev/install.sh | sh -s -- -b "$VENV_BIN" || {
            echo "Warning: failed to download Go Task; install manually from" \
                " https://taskfile.dev/installation/ and re-run setup" >&2
        }
    fi
fi
task --version || echo "task --version failed; continuing without Go Task" >&2

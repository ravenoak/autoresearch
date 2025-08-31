#!/usr/bin/env bash
# Usage: ./scripts/setup.sh
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

AR_SKIP_SMOKE_TEST=1 \
AR_EXTRAS="${AR_EXTRAS:-nlp ui vss parsers git distributed analysis llm}" \
    "$SCRIPT_DIR/setup_universal.sh" "$@"

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
        curl -sSL https://taskfile.dev/install.sh | sh -s -- -b "$VENV_BIN"
    fi
fi
"$TASK_BIN" --version >/dev/null 2>&1 || {
    echo "task --version failed; Go Task is required" >&2
    exit 1
}


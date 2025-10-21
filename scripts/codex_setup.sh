#!/usr/bin/env bash
# Usage: AR_EXTRAS="ui nlp" ./scripts/codex_setup.sh
# Codex-only environment bootstrap for this evaluation container; see AGENTS.md
# for repository-wide guidelines. Do not use or document this script outside the
# AGENTS.md system. For any other environment, use ./scripts/setup.sh.
# Installs the project in editable mode with development and test extras. It
# provisions the Task CLI through uvx when missing. Use AR_EXTRAS to specify
# optional extras.
set -euo pipefail

START_TIME=$(date +%s)
finish() {
    local exit_code=$?
    local end_time=$(date +%s)
    local elapsed=$((end_time - START_TIME))
    echo "codex_setup.sh finished in ${elapsed}s"
    if [ "$elapsed" -gt 900 ]; then
        echo "ERROR: setup exceeded 15-minute limit" >&2
        exit_code=1
    elif [ "$elapsed" -gt 600 ]; then
        echo "WARNING: setup exceeded 10-minute target" >&2
    fi
    exit "$exit_code"
}
trap finish EXIT

LOG_FILE="codex_setup.log"
: >"$LOG_FILE"
exec > >(tee -a "$LOG_FILE") 2>&1
echo "Streaming codex setup logs to $LOG_FILE"
set -x

if [[ "$(uname -s)" != "Linux" ]]; then
    echo "This script is intended for the Codex Linux environment." >&2
    exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/setup_common.sh"

echo "Starting Codex bootstrap at $(date -u +"%Y-%m-%dT%H:%M:%SZ")"

ensure_task_with_uvx \
    || { echo 'Failed to ensure Go Task availability.' >&2; exit 1; }

VENV_BIN="$PWD/.venv/bin"
ensure_venv_bin_on_path "$VENV_BIN"
export PATH="$VENV_BIN:$PATH"

mapfile -t codex_extras < <(collect_codex_extras)
echo "uv sync will include extras: ${codex_extras[*]}"

install_pyside6_system_deps

# Run platform detection and universal setup
AR_EXTRAS="${AR_EXTRAS:-}" "$SCRIPT_DIR/setup.sh" "$@"

ensure_pyside6_ready \
    || { echo 'PySide6 verification failed; inspect logs above for details.' >&2; exit 1; }

prefetch_codex_offline_artifacts \
    || { echo 'Failed to prefetch Codex offline assets.' >&2; exit 1; }

ensure_venv_bin_on_path "$PWD/.venv/bin"
echo ".venv/bin appended to PATH for this session"
echo "Persisted PATH helper at $(venv_path_snippet_file "$PWD/.venv/bin")."


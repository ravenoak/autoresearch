#!/usr/bin/env bash
# Usage: AR_EXTRAS="ui nlp" ./scripts/codex_maintenance.sh
# Refresh Codex evaluation containers resumed from cache. Ensures Go Task is
# available, keeps dependencies in sync with uv.lock, and revalidates Qt
# prerequisites without re-running the full bootstrap unless required.
set -euo pipefail

START_TIME=$(date +%s)
finish() {
    local exit_code=$?
    local end_time=$(date +%s)
    local elapsed=$((end_time - START_TIME))
    echo "codex_maintenance.sh finished in ${elapsed}s"
    if [ "$elapsed" -gt 900 ]; then
        echo "ERROR: maintenance exceeded 15-minute limit" >&2
        exit_code=1
    elif [ "$elapsed" -gt 600 ]; then
        echo "WARNING: maintenance exceeded 10-minute target" >&2
    fi
    exit "$exit_code"
}
trap finish EXIT

LOG_FILE="codex_maintenance.log"
: >"$LOG_FILE"
exec > >(tee -a "$LOG_FILE") 2>&1
set -x

if [[ "$(uname -s)" != "Linux" ]]; then
    echo "This script is intended for the Codex Linux environment." >&2
    exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/setup_common.sh"

echo "Starting Codex maintenance at $(date -u +"%Y-%m-%dT%H:%M:%SZ")"

if [ ! -d "$PWD/.venv" ]; then
    echo "Virtual environment missing; falling back to full setup." >&2
    exec "$SCRIPT_DIR/codex_setup.sh" "$@"
fi

ensure_task_with_uvx \
    || { echo 'Failed to ensure Go Task availability.' >&2; exit 1; }

ensure_venv_bin_on_path "$PWD/.venv/bin"
export PATH="$PWD/.venv/bin:$PATH"

install_pyside6_system_deps

extras_args=(--extra dev-minimal --extra test)
if [ -n "${AR_EXTRAS:-}" ]; then
    for extra in $AR_EXTRAS; do
        [ -n "$extra" ] || continue
        extras_args+=(--extra "$extra")
    done
fi

if ! uv sync --frozen "${extras_args[@]}"; then
    echo "Frozen dependency sync failed; attempting full uv sync." >&2
    uv sync "${extras_args[@]}"
fi

ensure_pyside6_ready \
    || { echo 'PySide6 verification failed; inspect logs above for details.' >&2; exit 1; }

prefetch_codex_offline_artifacts \
    || { echo 'Failed to prefetch Codex offline assets.' >&2; exit 1; }

echo "Persisted PATH helper at $(venv_path_snippet_file "$PWD/.venv/bin")."
echo "Maintenance complete. Activate the environment with 'source .venv/bin/activate'."

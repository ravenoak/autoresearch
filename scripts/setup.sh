#!/usr/bin/env bash
# Usage: AR_EXTRAS="nlp parsers" ./scripts/setup.sh
# Verify Python 3.12+, confirm Go Task and uv are installed, append .venv/bin to
# PATH, and sync dependencies.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

export PATH="$PATH:$(pwd)/.venv/bin"

EXTRAS=${AR_EXTRAS:-}

check_python() {
    local major minor
    major=$(python3 - <<'PY'
import sys
print(sys.version_info.major)
PY
)
    minor=$(python3 - <<'PY'
import sys
print(sys.version_info.minor)
PY
)
    if [ "$major" -lt 3 ] || { [ "$major" -eq 3 ] && [ "$minor" -lt 12 ]; }; then
        echo "Python 3.12+ required, found ${major}.${minor}" >&2
        exit 1
    fi
}

ensure_go_task() {
    if ! command -v task >/dev/null 2>&1; then
        echo "Go Task not found; running scripts/bootstrap.sh..." >&2
        "$SCRIPT_DIR/bootstrap.sh"
    fi
    if ! command -v task >/dev/null 2>&1; then
        echo "Go Task installation failed. See docs/installation.md for manual steps." >&2
        exit 1
    fi
    if ! task --version >/dev/null 2>&1; then
        echo "Go Task installation is broken; reinstall it." >&2
        exit 1
    fi
}

ensure_uv() {
    if ! command -v uv >/dev/null 2>&1; then
        echo "uv is required but not installed. See" >&2
        echo "https://github.com/astral-sh/uv for installation instructions." >&2
        exit 1
    fi
    if ! uv --version >/dev/null 2>&1; then
        echo "uv is installed but not functional; reinstall it." >&2
        exit 1
    fi
}

check_python
ensure_go_task
ensure_uv

extras_args=""
for extra in dev-minimal test $EXTRAS; do
    [ -n "$extra" ] && extras_args+=" --extra $extra"
done
echo "Syncing dependencies (dev-minimal test $EXTRAS)..."
if ! uv sync$extras_args; then
    echo "uv sync failed. Resolve the errors above and re-run." >&2
    exit 1
fi

echo "Environment ready. Activate with 'source .venv/bin/activate'."


#!/usr/bin/env bash
# Usage: AR_EXTRAS="nlp parsers" ./scripts/setup.sh
# Verify Python 3.12+, install Go Task if missing, append .venv/bin to PATH,
# and sync dependencies.

set -euo pipefail

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
        echo "Installing Go Task..."
        if ! curl -sSL https://taskfile.dev/install.sh \
            | sh -s -- -b "$(pwd)/.venv/bin" >/dev/null; then
            echo "Failed to install Go Task." >&2
            exit 1
        fi
    fi
    local version
    if ! version=$(task --version 2>/dev/null); then
        echo "Go Task installation is broken; reinstall it." >&2
        exit 1
    fi
    echo "$version"
}

ensure_uv() {
    if ! command -v uv >/dev/null 2>&1; then
        if ! python3 -m pip install uv >/dev/null; then
            echo "Failed to install uv. See https://github.com/astral-sh/uv" >&2
            exit 1
        fi
    fi
}

sync_deps() {
    local extras="dev-minimal test $EXTRAS"
    local args=""
    for extra in $extras; do
        [ -n "$extra" ] && args+=" --extra $extra"
    done
    echo "Syncing dependencies ($extras)..."
    if ! uv sync$args; then
        echo "uv sync failed. Resolve the errors above and re-run." >&2
        exit 1
    fi
}

check_python
ensure_go_task
ensure_uv
sync_deps

echo "Environment ready. Activate with 'source .venv/bin/activate'."


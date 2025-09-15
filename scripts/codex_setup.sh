#!/usr/bin/env bash
# Usage: AR_EXTRAS="ui nlp" ./scripts/codex_setup.sh
# Codex-only environment bootstrap for this evaluation container; see AGENTS.md
# for repository-wide guidelines. Do not use or document this script outside the
# AGENTS.md system. For any other environment, use ./scripts/setup.sh.
# Installs the project in editable mode with development and test extras. It
# invokes bootstrap.sh to install Go Task when missing. Use AR_EXTRAS to
# specify optional extras.
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
exec > >(tee -a "$LOG_FILE") 2>&1
set -x

if [[ "$(uname -s)" != "Linux" ]]; then
    echo "This script is intended for the Codex Linux environment." >&2
    exit 1
fi

SCRIPT_DIR="$(dirname "$0")"
source "$SCRIPT_DIR/setup_common.sh"

# Ensure Go Task is available before platform-specific setup
"$SCRIPT_DIR/bootstrap.sh"
ensure_venv_bin_on_path "$PWD/.venv/bin"
if ! task --version >/dev/null 2>&1; then
    echo "Go Task installation failed. See docs/installation.md for manual steps." >&2
    exit 1
fi

# Run platform detection and universal setup
AR_EXTRAS="${AR_EXTRAS:-}" "$SCRIPT_DIR/setup.sh" "$@"

# Codex-specific offline model preparation
if uv pip show sentence-transformers >/dev/null 2>&1; then
    retry 3 uv run python -c \
        "from sentence_transformers import SentenceTransformer;\
SentenceTransformer('all-MiniLM-L6-v2')"
fi

if uv pip show spacy >/dev/null 2>&1; then
    retry 3 uv run python -m spacy download en_core_web_sm
fi

uv run python -c "import owlrl" \
    || { echo 'Failed to pre-load ontology reasoner.' >&2; exit 1; }

ensure_venv_bin_on_path "$PWD/.venv/bin"
echo ".venv/bin appended to PATH for this session"
export PATH="$(pwd)/.venv/bin:$PATH"


#!/usr/bin/env bash
# Usage: AR_EXTRAS="ui nlp" ./scripts/codex_setup.sh
# Codex-only environment bootstrap for this evaluation container; see AGENTS.md
# for repository-wide guidelines. Do not use or document this script outside the
# AGENTS.md system. For any other environment, use ./scripts/setup.sh.
# Installs the project in editable mode with development and test extras. Use
# AR_EXTRAS to specify optional extras.
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

source "$(dirname "$0")/setup_common.sh"

retry() {
    local -r max_attempts="$1"; shift
    local attempt=1
    until "$@"; do
        if (( attempt == max_attempts )); then
            echo "Command failed after $attempt attempts: $*" >&2
            return 1
        fi
        echo "Attempt $attempt failed: $*. Retrying..." >&2
        attempt=$((attempt + 1))
        sleep 2
    done
}

# Ensure uv is installed
if ! command -v uv >/dev/null 2>&1; then
    curl -LsSf https://astral.sh/uv/install.sh | sh -s -- --quiet
    export PATH="$HOME/.local/bin:$PATH"
fi
command -v uv >/dev/null 2>&1 || { echo "uv is required but missing" >&2; exit 1; }

# Install system packages
export DEBIAN_FRONTEND=noninteractive
retry 3 apt-get update
retry 3 apt-get install -y \
    build-essential python3-dev python3-venv cmake pkg-config git \
    libssl-dev libffi-dev libxml2-dev libargon2-dev libblas-dev \
    liblapack-dev libopenblas-dev liblmdb-dev libz3-dev \
    libcurl4-openssl-dev
retry 3 apt-get clean
rm -rf /var/lib/apt/lists/*

# Delegate remaining setup to the universal script
AR_EXTRAS="${AR_EXTRAS:-}" ./scripts/setup.sh

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

# Cache DuckDB extensions for offline use
retry 3 uv run python scripts/download_duckdb_extensions.py \
    --output-dir ./extensions || \
    echo 'DuckDB extension download failed; continuing.'

ensure_venv_bin_on_path "$PWD/.venv/bin"
echo ".venv/bin appended to PATH for this session"

cat <<'EOF'
To activate the virtual environment, run:
  source .venv/bin/activate
EOF

task --version


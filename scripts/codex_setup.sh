#!/usr/bin/env bash
set -euo pipefail
set -o pipefail

LOG_FILE="codex_setup.log"
exec > >(tee -a "$LOG_FILE") 2>&1
set -x

# Pre-flight: ensure uv is installed
if ! command -v uv >/dev/null 2>&1; then
    echo "uv not found. Installing..."
    curl -LsSf https://astral.sh/uv/install.sh | sh -s -- --quiet
    export PATH="$HOME/.local/bin:$PATH"
fi

if ! command -v uv >/dev/null 2>&1; then
    echo "uv is required but was not installed successfully" >&2
    exit 1
fi

# Ensure Python 3.12 is available before proceeding
if ! command -v python3.12 >/dev/null 2>&1; then
    echo "python3.12 is required but was not found in PATH" >&2
    exit 1
fi

echo "Setting up Codex environment..."

export DEBIAN_FRONTEND=noninteractive
apt-get update && echo "apt-get update completed" || { echo "apt-get update failed" >&2; exit 1; }
apt-get install -y \
        build-essential python3-dev python3-venv cmake pkg-config git libssl-dev libffi-dev libxml2-dev libargon2-dev libblas-dev liblapack-dev libopenblas-dev liblmdb-dev libz3-dev libcurl4-openssl-dev \
    && echo "apt-get install completed" || { echo "apt-get install failed" >&2; exit 1; }
apt-get clean && echo "apt-get clean completed" || { echo "apt-get clean failed" >&2; exit 1; }
rm -rf /var/lib/apt/lists/*

# Install Go Task for running Taskfile commands if not already installed
if ! command -v task >/dev/null 2>&1; then
    curl -sL https://taskfile.dev/install.sh | sh -s -- -b /usr/local/bin
fi

# Verify Go Task was installed
if [ ! -x /usr/local/bin/task ]; then
    echo "Go Task not found at /usr/local/bin/task." >&2
    echo "Re-run: curl -sL https://taskfile.dev/install.sh | sh -s -- -b /usr/local/bin" >&2
    exit 1
fi

# Run the main setup script to install all extras needed for testing
./scripts/setup.sh full,parsers,git,llm,dev,test

# Ensure duckdb-extension-vss is installed for DuckDB vector search support
if ! uv pip show duckdb-extension-vss >/dev/null 2>&1; then
    uv pip install duckdb-extension-vss && echo "duckdb-extension-vss installed" \
        || { echo 'Failed to install duckdb-extension-vss' >&2; exit 1; }
fi

# Confirm required extras are installed
echo "Verifying required extras..."
missing=0
for pkg in pytest-cov hypothesis tomli_w duckdb-extension-vss a2a-sdk GitPython pdfminer-six python-docx sentence-transformers transformers; do
    if ! uv pip show "$pkg" >/dev/null 2>&1; then
        echo "Missing required package: $pkg" >&2
        missing=1
    fi
done
if [ "$missing" -ne 0 ]; then
    echo "Required packages are missing. Check setup logs." >&2
    exit 1
fi
uv pip list | grep -E 'pytest-cov|hypothesis|tomli_w|duckdb-extension-vss|a2a-sdk|GitPython|pdfminer-six|python-docx|sentence-transformers|transformers'

# Helper for retrying flaky network operations
retry() {
    local -r max_attempts="$1"; shift
    local attempt=1
    while (( attempt <= max_attempts )); do
        if "$@"; then
            return 0
        fi
        if (( attempt == max_attempts )); then
            echo "Command failed after $attempt attempts: $*" >&2
            return 1
        fi
        echo "Attempt $attempt failed: $*. Retrying..." >&2
        attempt=$((attempt + 1))
        sleep 2
    done
}

# Pre-download models so tests can run without network access
SENTENCE_MODEL_DIR="$HOME/.cache/torch/sentence_transformers/all-MiniLM-L6-v2"
retry 3 uv run python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')" \
    && echo "SentenceTransformer model downloaded" \
    || { echo 'Failed to download SentenceTransformer model.' >&2; exit 1; }
if [ ! -d "$SENTENCE_MODEL_DIR" ]; then
    echo "SentenceTransformer model not found at $SENTENCE_MODEL_DIR" >&2
    exit 1
fi

retry 3 uv run python -m spacy download en_core_web_sm \
    && echo "spaCy en_core_web_sm model downloaded" \
    || { echo 'Failed to download spaCy model.' >&2; exit 1; }
SPACY_MODEL_DIR=$(uv run python - <<'PY'
import os, en_core_web_sm
print(os.path.dirname(en_core_web_sm.__file__))
PY
)
if [ ! -d "$SPACY_MODEL_DIR" ]; then
    echo "spaCy model en_core_web_sm not found at $SPACY_MODEL_DIR" >&2
    exit 1
fi

# Pre-load ontology reasoner so tests can run offline
uv run python -c "import owlrl" || { echo 'Failed to pre-load ontology reasoner.' >&2; exit 1; }

# Cache DuckDB extensions for offline use (vss by default)
retry 3 uv run python scripts/download_duckdb_extensions.py --output-dir ./extensions \
    && echo "DuckDB extensions downloaded" \
    || { echo 'Failed to download DuckDB extensions.' >&2; exit 1; }
if ! find ./extensions -type f -name '*.duckdb_extension' | grep -q .; then
    echo 'DuckDB extensions not found in ./extensions' >&2
    exit 1
fi

# All Python setup is handled by setup.sh using uv pip


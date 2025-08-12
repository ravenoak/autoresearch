#!/usr/bin/env bash
set -euo pipefail

LOG_FILE="codex_setup.log"
exec > >(tee -a "$LOG_FILE") 2>&1
set -x

# NOTE: Keep this script in sync with AGENTS.md.
# When tooling or helper scripts change, update both this file and AGENTS.md.

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
if apt-get update; then
    echo "apt-get update completed"
else
    echo "apt-get update failed" >&2
    exit 1
fi
if apt-get install -y \
        build-essential python3-dev python3-venv cmake pkg-config git libssl-dev libffi-dev libxml2-dev libargon2-dev libblas-dev liblapack-dev libopenblas-dev liblmdb-dev libz3-dev libcurl4-openssl-dev \
    ; then
    echo "apt-get install completed"
else
    echo "apt-get install failed" >&2
    exit 1
fi
if apt-get clean; then
    echo "apt-get clean completed"
else
    echo "apt-get clean failed" >&2
    exit 1
fi
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
    if uv pip install duckdb-extension-vss; then
        echo "duckdb-extension-vss installed"
    else
        echo 'Failed to install duckdb-extension-vss' >&2
        exit 1
    fi
fi

# Confirm required extras are installed
echo "Verifying required extras..."
missing=0
missing_pkgs=""
for pkg in pytest pytest-bdd pytest-httpx pytest-cov hypothesis tomli_w freezegun duckdb-extension-vss a2a-sdk GitPython pdfminer-six python-docx sentence-transformers transformers spacy bertopic; do
    if ! uv pip show "$pkg" >/dev/null 2>&1; then
        echo "Missing required package: $pkg" >&2
        missing=1
        missing_pkgs+="$pkg "
    fi
done
if [ "$missing" -ne 0 ]; then
    echo "ERROR: Missing dev packages: $missing_pkgs" >&2
    exit 1
fi
uv pip list | grep -E 'pytest(-bdd|-httpx)?|pytest-cov|hypothesis|tomli_w|freezegun|duckdb-extension-vss|a2a-sdk|GitPython|pdfminer-six|python-docx|sentence-transformers|transformers|spacy|bertopic'

# Ensure VECTOR_EXTENSION_PATH is configured
if ! grep -q "VECTOR_EXTENSION_PATH" .env; then
    echo "VECTOR_EXTENSION_PATH not set in .env" >&2
    exit 1
fi

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
if retry 3 uv run python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"; then
    echo "SentenceTransformer model downloaded"
else
    echo 'Failed to download SentenceTransformer model.' >&2
    exit 1
fi
if [ ! -d "$SENTENCE_MODEL_DIR" ]; then
    echo "SentenceTransformer model not found at $SENTENCE_MODEL_DIR" >&2
    exit 1
fi

if retry 3 uv run python -m spacy download en_core_web_sm; then
    echo "spaCy en_core_web_sm model downloaded"
else
    echo 'Failed to download spaCy model.' >&2
    exit 1
fi
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
if retry 3 uv run python scripts/download_duckdb_extensions.py --output-dir ./extensions; then
    echo "DuckDB extensions downloaded"
else
    echo 'Failed to download DuckDB extensions.' >&2
    exit 1
fi
if ! find ./extensions -type f -name '*.duckdb_extension' | grep -q .; then
    echo 'DuckDB extensions not found in ./extensions' >&2
    exit 1
fi

# All Python setup is handled by setup.sh using uv pip


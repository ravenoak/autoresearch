#!/usr/bin/env bash
set -euo pipefail

LOG_FILE="codex_setup.log"
exec > >(tee -a "$LOG_FILE") 2>&1
set -x

# NOTE: Keep this script in sync with AGENTS.md.
# When tooling, helper scripts, or test directories change, update both this
# file and AGENTS.md so new test requirements are captured here.

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

# Ensure Python 3.12 or newer is available before proceeding
if ! command -v python3 >/dev/null 2>&1; then
    echo "python3 is required but was not found in PATH" >&2
    exit 1
fi

PYTHON_BIN=$(command -v python3)
PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info[0]}.{sys.version_info[1]}")')
if ! python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3, 12) else 1)' >/dev/null 2>&1; then
    echo "Python 3.12 or newer is required. Found $PYTHON_VERSION. Installing Python 3.12..." >&2
    uv python install 3.12
    PYTHON_BIN=$(uv python find 3.12)
    PYTHON_VERSION=$("$PYTHON_BIN" -c 'import sys; print(f"{sys.version_info[0]}.{sys.version_info[1]}")')
    PATH="$(dirname "$PYTHON_BIN"):$PATH"
fi
echo "Using Python $PYTHON_VERSION from $PYTHON_BIN"

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

# Run the main setup script to install all extras needed for testing
./scripts/setup.sh

# Install Go Task inside the virtual environment
curl -sL https://taskfile.dev/install.sh | sh -s -- -b ./.venv/bin

# Sync all development extras in editable mode
uv pip install -e '.[full,parsers,git,llm,dev]'

# Install pre-downloaded packages for offline use. Place wheel files in
# $WHEELS_DIR and source archives in $ARCHIVES_DIR. See AGENTS.md for
# details.
if [ -n "${WHEELS_DIR:-}" ] && [ -d "$WHEELS_DIR" ]; then
    if ls "$WHEELS_DIR"/*.whl >/dev/null 2>&1; then
        echo "Installing wheels from $WHEELS_DIR"
        uv pip install --no-index --find-links "$WHEELS_DIR" "$WHEELS_DIR"/*.whl
    fi
fi

if [ -n "${ARCHIVES_DIR:-}" ] && [ -d "$ARCHIVES_DIR" ]; then
    if ls "$ARCHIVES_DIR"/*.tar.gz >/dev/null 2>&1; then
        echo "Installing archives from $ARCHIVES_DIR"
        uv pip install --no-index --find-links "$ARCHIVES_DIR" "$ARCHIVES_DIR"/*.tar.gz
    fi
fi

# Verify CLI tools resolve inside the virtual environment
source .venv/bin/activate
missing_tools=()
for cmd in task flake8 pytest mypy; do
    cmd_path=$(command -v "$cmd" || true)
    if [[ "$cmd_path" != "$VIRTUAL_ENV"/* ]]; then
        echo "$cmd is not resolved inside .venv: ${cmd_path:-not found}" >&2
        missing_tools+=("$cmd")
        continue
    fi
    if ! version=$("$cmd" --version 2>&1); then
        echo "$cmd is not installed or failed to report a version" >&2
        missing_tools+=("$cmd")
    else
        echo "$cmd version: $version"
    fi
done

# Ensure required development packages are installed in the virtual environment
required_pkgs=(flake8 pytest-bdd freezegun tomli_w hypothesis pytest-cov pydantic)
missing_pkgs=()
for pkg in "${required_pkgs[@]}"; do
    if ! uv pip show "$pkg" >/dev/null 2>&1; then
        echo "$pkg is not installed in .venv" >&2
        missing_pkgs+=("$pkg")
    fi
done

if (( ${#missing_tools[@]} )) || (( ${#missing_pkgs[@]} )); then
    echo "Missing CLI tools: ${missing_tools[*]}" >&2
    echo "Missing packages: ${missing_pkgs[*]}" >&2
    deactivate
    uv pip install -e '.[full,parsers,git,llm,dev]'
    echo "ERROR: Required tools or packages missing after install" >&2
    exit 1
fi

# Post-install version checks
task --version >/dev/null 2>&1 || { echo 'task is required but missing' >&2; exit 1; }
flake8 --version >/dev/null 2>&1 || { echo 'flake8 is required but missing' >&2; exit 1; }
mypy --version >/dev/null 2>&1 || { echo 'mypy is required but missing' >&2; exit 1; }
pytest --version >/dev/null 2>&1 || { echo 'pytest is required but missing' >&2; exit 1; }
python - <<'PY' || { echo 'pytest-bdd is required but missing' >&2; exit 1; }
import pydantic, importlib.metadata
print(pydantic.__version__)
print(importlib.metadata.version('pytest-bdd'))
PY

# Confirm key packages import successfully
python - <<'PY'
import freezegun, tomli_w, hypothesis, pytest_cov, pytest_bdd
PY
deactivate

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
# Tests marked `requires_ui`, `requires_vss`, `requires_git`, and `requires_nlp`
# depend on these packages. Update this list and AGENTS.md when adding new
# markers or optional test extras.
echo "Verifying required extras..."
missing=0
missing_pkgs=""
for pkg in pytest pytest-bdd pytest-httpx pytest-cov flake8 mypy pydantic hypothesis tomli_w freezegun \
    duckdb-extension-vss a2a-sdk GitPython pdfminer-six python-docx sentence-transformers \
    transformers spacy bertopic fastapi responses uvicorn psutil; do
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
uv pip list | grep -E 'pytest(-bdd|-httpx)?|pytest-cov|flake8|mypy|hypothesis|tomli_w|freezegun|responses|uvicorn|psutil|duckdb-extension-vss|a2a-sdk|GitPython|pdfminer-six|python-docx|sentence-transformers|transformers|spacy|bertopic|fastapi'

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

# Ensure pip is available for spaCy model download
uv pip install pip >/dev/null
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

# Cache DuckDB extensions for offline use (vss by default).
# Binary extension files are downloaded here and kept out of version control.
if retry 3 uv run python scripts/download_duckdb_extensions.py --output-dir ./extensions; then
    echo "DuckDB extensions downloaded"
else
    echo 'Failed to download DuckDB extensions.' >&2
    exit 1
fi
# Export the path to the VSS extension for downstream tools. If no real
# extension is available, fall back to the stub so tests can run without
# vector search.
if [ -z "${VECTOR_EXTENSION_PATH:-}" ]; then
    VSS_PATH=$(find ./extensions -type f -name 'vss*.duckdb_extension' | head -n 1)
    if [ -n "$VSS_PATH" ]; then
        export VECTOR_EXTENSION_PATH="$VSS_PATH"
        echo "VECTOR_EXTENSION_PATH set to $VECTOR_EXTENSION_PATH"
    else
        export VECTOR_EXTENSION_PATH="extensions/vss_stub.duckdb_extension"
        mkdir -p "$(dirname "$VECTOR_EXTENSION_PATH")"
        : > "$VECTOR_EXTENSION_PATH"
        echo "VECTOR_EXTENSION_PATH defaulted to stub at $VECTOR_EXTENSION_PATH"
    fi
else
    echo "VECTOR_EXTENSION_PATH already set to $VECTOR_EXTENSION_PATH"
fi

# All Python setup is handled by setup.sh using uv pip


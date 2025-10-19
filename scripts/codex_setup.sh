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

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/setup_common.sh"

ensure_env_var() {
    local key="$1"
    local value="$2"
    for env_file in .env.offline .env; do
        if [ ! -f "$env_file" ]; then
            printf '%s=%s\n' "$key" "$value" >"$env_file"
            continue
        fi
        if grep -q "^${key}=" "$env_file"; then
            sed -i.bak "s|^${key}=.*|${key}=${value}|" "$env_file"
            rm -f "$env_file.bak"
        else
            printf '%s=%s\n' "$key" "$value" >>"$env_file"
        fi
    done
}

install_pyside6_system_deps() {
    if ! command -v apt-get >/dev/null 2>&1; then
        echo "apt-get not available; install PySide6 runtime dependencies manually." >&2
        return
    fi
    if [[ "$(id -u)" -ne 0 ]]; then
        echo "Skipping PySide6 system dependencies; root privileges required to install packages." >&2
        return
    fi

    export DEBIAN_FRONTEND=noninteractive
    retry 3 apt-get update

    local qt_packages=(
        libegl1
        libgl1
        libglib2.0-0
        libdbus-1-3
        libnss3
        libxkbcommon-x11-0
        libxcb-cursor0
        libxcomposite1
        libxcursor1
        libxdamage1
        libxfixes3
        libxi6
        libxinerama1
        libxkbfile1
        libxrandr2
        libxss1
        libxtst6
        libfontconfig1
        libsm6
        libice6
    )

    local audio_pkg=""
    if apt-cache show libasound2t64 >/dev/null 2>&1; then
        audio_pkg="libasound2t64"
    elif apt-cache show libasound2 >/dev/null 2>&1; then
        audio_pkg="libasound2"
    fi
    if [ -n "$audio_pkg" ]; then
        qt_packages+=("$audio_pkg")
    fi

    retry 3 apt-get install -y "${qt_packages[@]}"
    retry 3 apt-get clean
    rm -rf /var/lib/apt/lists/*
}

ensure_pyside6_ready() {
    if ! uv pip show PySide6 >/dev/null 2>&1; then
        retry 3 uv pip install "PySide6>=6.6.0"
    fi
    if ! uv pip show pytest-qt >/dev/null 2>&1; then
        retry 3 uv pip install pytest-qt
    fi

    ensure_env_var "QT_QPA_PLATFORM" "offscreen"
    ensure_env_var "QTWEBENGINE_CHROMIUM_FLAGS" "--no-sandbox --disable-gpu --disable-software-rasterizer"
    ensure_env_var "QTWEBENGINE_DISABLE_SANDBOX" "1"
    ensure_env_var "AUTORESEARCH_SUPPRESS_DIALOGS" "1"

    if ! env QT_QPA_PLATFORM=offscreen \
        QTWEBENGINE_CHROMIUM_FLAGS="--no-sandbox --disable-gpu --disable-software-rasterizer" \
        QTWEBENGINE_DISABLE_SANDBOX=1 \
        AUTORESEARCH_SUPPRESS_DIALOGS=1 \
        uv run python - <<'PY'; then
from PySide6.QtWidgets import QApplication
from PySide6.QtWebEngineWidgets import QWebEngineView

app = QApplication([])
view = QWebEngineView()
view.deleteLater()
app.quit()
PY
        echo "PySide6 sanity check failed. Ensure Qt dependencies are available." >&2
        return 1
    fi
}

# Ensure Go Task is available before platform-specific setup
"$SCRIPT_DIR/bootstrap.sh"
VENV_BIN="$PWD/.venv/bin"
ensure_venv_bin_on_path "$VENV_BIN"
export PATH="$VENV_BIN:$PATH"
if ! task --version >/dev/null 2>&1; then
    echo "Go Task installation failed. See docs/installation.md for manual steps." >&2
    exit 1
fi

install_pyside6_system_deps

# Run platform detection and universal setup
AR_EXTRAS="${AR_EXTRAS:-}" "$SCRIPT_DIR/setup.sh" "$@"

ensure_pyside6_ready \
    || { echo 'PySide6 verification failed; inspect logs above for details.' >&2; exit 1; }

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
echo "Persisted PATH helper at $(venv_path_snippet_file "$PWD/.venv/bin")."


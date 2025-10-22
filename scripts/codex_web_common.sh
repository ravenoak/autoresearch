#!/usr/bin/env bash
# Usage: source scripts/codex_web_common.sh
# Codex Web shared helpers for setup and maintenance workflows.
set -euo pipefail

install_pyside6_system_deps() {
    # Reduce provisioning latency by skipping apt operations when all
    # dependencies are already present. The Codex container runs as root, but
    # bail out gracefully if that assumption changes.
    if ! command -v apt-get >/dev/null 2>&1; then
        echo "apt-get not available; install PySide6 runtime dependencies manually." >&2
        return 0
    fi
    if [[ "$(id -u)" -ne 0 ]]; then
        echo "Skipping PySide6 system dependencies; root privileges required." >&2
        return 0
    fi

    local package_groups=(
        "libegl1"
        "libgl1-mesa-glx|libgl1|libgl1-mesa-dri"
        "libglib2.0-0"
        "libdbus-1-3"
        "libnss3"
        "libxkbcommon-x11-0"
        "libxcb-cursor0"
        "libxcomposite1"
        "libxcursor1"
        "libxdamage1"
        "libxfixes3"
        "libxi6"
        "libxinerama1"
        "libxkbfile1"
        "libxrandr2"
        "libxss1"
        "libxtst6"
        "libfontconfig1"
        "libsm6"
        "libice6"
    )

    package_groups+=("libasound2t64|libasound2")

    local missing_groups=()
    local group
    for group in "${package_groups[@]}"; do
        IFS='|' read -r -a options <<<"$group"
        local installed_option=""
        local option
        for option in "${options[@]}"; do
            if dpkg -s "$option" >/dev/null 2>&1; then
                installed_option="$option"
                break
            fi
        done
        if [ -z "$installed_option" ]; then
            missing_groups+=("$group")
        fi
    done

    if ((${#missing_groups[@]} == 0)); then
        echo "PySide6 runtime dependencies already installed; skipping apt-get." >&2
        return 0
    fi

    export DEBIAN_FRONTEND=noninteractive
    retry 3 apt-get update

    local install_queue=()
    for group in "${missing_groups[@]}"; do
        IFS='|' read -r -a options <<<"$group"
        local candidate=""
        local option
        for option in "${options[@]}"; do
            if apt-cache show "$option" >/dev/null 2>&1; then
                candidate="$option"
                break
            fi
        done
        if [ -z "$candidate" ]; then
            echo "Warning: unable to resolve package options: $group" >&2
            continue
        fi
        install_queue+=("$candidate")
    done

    if ((${#install_queue[@]} == 0)); then
        echo "Warning: no installable PySide6 packages detected after update." >&2
        return 0
    fi

    retry 3 apt-get install -y "${install_queue[@]}"
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

prefetch_codex_offline_artifacts() {
    local status=0

    if uv pip show sentence-transformers >/dev/null 2>&1; then
        retry 3 uv run python -c \
            "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')" \
            || status=1
    fi

    if uv pip show spacy >/dev/null 2>&1; then
        retry 3 uv run python -m spacy download en_core_web_sm || status=1
    fi

    if uv pip show owlrl >/dev/null 2>&1; then
        if ! uv run python -c "import owlrl"; then
            echo "Failed to pre-load ontology reasoner (owlrl)." >&2
            status=1
        fi
    else
        echo "owlrl not installed; ensure project dependencies are synced." >&2
        status=1
    fi

    return $status
}

collect_codex_extras() {
    local extras=(dev-minimal test)
    if [ -n "${AR_EXTRAS:-}" ]; then
        local extra
        for extra in $AR_EXTRAS; do
            [ -n "$extra" ] && extras+=("$extra")
        done
    fi

    declare -A seen=()
    local filtered=()
    local entry
    for entry in "${extras[@]}"; do
        [ -n "$entry" ] || continue
        if [ "${AR_SKIP_GPU:-1}" = "1" ] && [ "$entry" = "gpu" ]; then
            continue
        fi
        if [ -n "${seen[$entry]:-}" ]; then
            continue
        fi
        seen[$entry]=1
        filtered+=("$entry")
    done

    printf '%s\n' "${filtered[@]}"
}

uv_sync_with_codex_extras() {
    local extra_args=()
    local extras=()
    local extra
    mapfile -t extras < <(collect_codex_extras)

    if [ ${#extras[@]} -eq 0 ]; then
        extras=(dev-minimal test)
    fi

    local find_links=()
    for extra in "${extras[@]}"; do
        extra_args+=(--extra "$extra")
        if [ "$extra" = "gpu" ] && [ -d wheels/gpu ]; then
            find_links=(--find-links wheels/gpu)
        fi
    done

    uv sync "$@" "${find_links[@]}" "${extra_args[@]}"
}

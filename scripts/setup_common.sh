#!/usr/bin/env bash
# Usage: source scripts/setup_common.sh
# Shared helpers for environment setup scripts.
set -euo pipefail

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

ensure_env_var() {
    local key="$1"
    local value="$2"
    for env_file in .env.offline .env; do
        if [ ! -f "$env_file" ]; then
            printf '%s=%s\n' "$key" "$value" >"$env_file"
            continue
        fi

        if grep -q "^${key}=${value}$" "$env_file"; then
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

ensure_uv() {
    if ! command -v uv >/dev/null 2>&1; then
        curl -LsSf https://astral.sh/uv/install.sh | sh -s -- --quiet
        export PATH="$HOME/.local/bin:$PATH"
    fi
    command -v uv >/dev/null 2>&1 \
        || { echo "uv is required but missing" >&2; return 1; }
    uv_version=$(uv --version | awk '{print $2}')
    uv_major=${uv_version%%.*}
    uv_minor=${uv_version#*.}
    uv_minor=${uv_minor%%.*}
    if [ "$uv_major" -lt 0 ] || { [ "$uv_major" -eq 0 ] && [ "$uv_minor" -lt 7 ]; }; then
        echo "uv 0.7.0 or newer required, found $uv_version" >&2
        return 1
    fi
}

install_dev_test_extras() {
    local extras="dev test"
    if [ -n "${AR_EXTRAS:-}" ]; then
        extras="$extras ${AR_EXTRAS}"
    fi
    if [ "${AR_SKIP_GPU:-1}" = "1" ]; then
        extras=$(printf '%s\n' $extras | grep -v '^gpu$' | xargs)
    fi
    local find_links=""
    if printf '%s\n' $extras | grep -q '^gpu$' && [ -d wheels/gpu ]; then
        # Use local wheels to avoid slow source builds for GPU dependencies.
        find_links="--find-links wheels/gpu"
    fi
    echo "Installing extras via uv sync --python-platform x86_64-manylinux_2_28" \
        "$find_links --extra ${extras// / --extra }"
    uv sync --python-platform x86_64-manylinux_2_28 $find_links \
        $(for e in $extras; do printf -- '--extra %s ' "$e"; done)
    uv pip install -e .
}

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

    local missing_packages=()
    local pkg
    for pkg in "${qt_packages[@]}"; do
        if ! dpkg -s "$pkg" >/dev/null 2>&1; then
            missing_packages+=("$pkg")
        fi
    done

    if ((${#missing_packages[@]} == 0)); then
        echo "PySide6 runtime dependencies already installed; skipping apt-get." >&2
        return 0
    fi

    export DEBIAN_FRONTEND=noninteractive
    retry 3 apt-get update
    retry 3 apt-get install -y "${missing_packages[@]}"
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

ensure_task_with_uvx() {
    ensure_uv

    local venv_bin="$PWD/.venv/bin"
    mkdir -p "$venv_bin"
    ensure_venv_bin_on_path "$venv_bin"

    if command -v task >/dev/null 2>&1; then
        if ! task --version >/dev/null 2>&1; then
            echo "Go Task detected but unusable; reinstall or remove it." >&2
            return 1
        fi
        return 0
    fi

    local task_wrapper="$venv_bin/task"
    cat >"$task_wrapper" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
exec uvx --from go-task-bin task "$@"
EOF
    chmod +x "$task_wrapper"
    export PATH="$venv_bin:$PATH"

    if ! task --version >/dev/null 2>&1; then
        echo "Failed to provision Task via uvx. See docs/installation.md for manual steps." >&2
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


absolute_path() {
    local path="$1"
    if command -v python3 >/dev/null 2>&1; then
        python3 - "$path" <<'PY'
import os
import sys
print(os.path.abspath(sys.argv[1]))
PY
        return 0
    fi
    if [ "${path#/}" != "$path" ]; then
        printf '%s\n' "$path"
    else
        printf '%s/%s\n' "$(pwd)" "$path"
    fi
}

venv_path_snippet_file() {
    local venv_bin="$1"
    local abs_bin
    abs_bin=$(absolute_path "$venv_bin")
    local repo_root="${abs_bin%/.venv/bin}"
    printf '%s/.autoresearch/path.sh\n' "$repo_root"
}

venv_path_snippet() {
    local venv_bin="$1"
    local abs_bin
    abs_bin=$(absolute_path "$venv_bin")
    cat <<EOF
# Autogenerated by Autoresearch setup helpers; add to your shell profile.
if [ -d "$abs_bin" ]; then
    case ":\$PATH:" in
        *":$abs_bin:"*) ;;
        *) export PATH="$abs_bin:\$PATH" ;;
    esac
fi
EOF
}

persist_venv_path_snippet() {
    local venv_bin="$1"
    local snippet_file
    snippet_file=$(venv_path_snippet_file "$venv_bin")
    mkdir -p "$(dirname "$snippet_file")"
    venv_path_snippet "$venv_bin" >"$snippet_file"
}

ensure_venv_bin_on_path() {
    local venv_bin="${1:-.venv/bin}"
    case ":$PATH:" in
        *":$venv_bin:"*) ;;
        *) export PATH="$venv_bin:$PATH" ;;
    esac
    persist_venv_path_snippet "$venv_bin"
}

# Compose extras for Codex-managed scripts, deduplicating and honoring
# AR_SKIP_GPU when set.
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

# Run uv sync with the resolved Codex extras, propagating additional flags
# such as --frozen when provided.
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

record_vector_extension_path() {
    local path="$1"
    for env_file in .env .env.offline; do
        if [ ! -f "$env_file" ]; then
            echo "VECTOR_EXTENSION_PATH=$path" >"$env_file"
        elif grep -q "VECTOR_EXTENSION_PATH" "$env_file"; then
            sed -i.bak \
                "s|VECTOR_EXTENSION_PATH=.*|VECTOR_EXTENSION_PATH=$path|" \
                "$env_file" && rm -f "$env_file.bak"
        else
            echo "VECTOR_EXTENSION_PATH=$path" >>"$env_file"
        fi
    done
}

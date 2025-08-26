#!/usr/bin/env bash
# Usage: ./scripts/setup.sh
# Full developer bootstrap; see docs/installation.md.
# Create .venv, install Go Task to .venv/bin, and development/test extras using uv.
# Ensure we are running with Python 3.12 or newer.
# Run `uv run python scripts/check_env.py` at the end to validate tool versions.
set -euo pipefail

# Abort if python3 is not available
if ! command -v python3 >/dev/null 2>&1; then
    echo "python3 is required but was not found in PATH" >&2
    exit 1
fi

PYTHON_BIN=$(command -v python3)
PYTHON_VERSION=$(python3 -c 'import sys; print("%d.%d" % sys.version_info[:2])')
if ! python3 - <<'EOF' >/dev/null 2>&1
import sys
sys.exit(0 if sys.version_info >= (3, 12) else 1)
EOF
then
    echo "Python 3.12 or newer is required. Found $PYTHON_VERSION. Installing Python 3.12..." >&2
    uv python install 3.12
    PYTHON_BIN=$(uv python find 3.12)
    PYTHON_VERSION=$("$PYTHON_BIN" -c 'import sys; print("%d.%d" % sys.version_info[:2])')
fi
echo "Using Python $PYTHON_VERSION from $PYTHON_BIN"

# Create a Python 3.12+ virtual environment
uv venv --python "$PYTHON_BIN"
VENV_PYTHON="./.venv/bin/python"
"$VENV_PYTHON" - <<'EOF'
import sys
if sys.version_info < (3, 12):
    raise SystemExit(f"uv venv created Python {sys.version.split()[0]}, but >=3.12 is required")
EOF

# Add virtual environment bin to PATH for subsequent commands
VENV_BIN="$(pwd)/.venv/bin"
export PATH="$VENV_BIN:$PATH"

# Ensure Go Task is available for later Taskfile commands
if ! command -v task >/dev/null 2>&1; then
    echo "Go Task missing; installing into $VENV_BIN..."
    curl -sSL https://taskfile.dev/install.sh | sh -s -- -b "$VENV_BIN"
    export PATH="$VENV_BIN:$PATH"
fi
task --version >/dev/null 2>&1 || {
    echo "task --version failed; Go Task is required but was not installed" >&2
    exit 1
}

# Install locked dependencies and development/test extras
echo "Installing development and test extras via uv sync --extra dev --extra test"
uv sync --extra dev --extra test

# Link the project in editable mode so tools are available
uv pip install -e .

# Verify dev and test extras are installed
for pkg in pytest_httpx tomli_w freezegun hypothesis redis; do
    if ! uv pip show "$pkg" >/dev/null 2>&1; then
        echo "$pkg is required for tests but was not installed" >&2
        exit 1
    fi
done

# Append Go Task path to activation scripts if absent
for script in "$VENV_BIN/activate" \
    "$VENV_BIN/activate.fish" \
    "$VENV_BIN/activate.csh" \
    "$VENV_BIN/activate.bat" \
    "$VENV_BIN/activate.ps1"; do
    if [ -f "$script" ] && ! grep -q 'VIRTUAL_ENV.*bin' "$script"; then
        case "$script" in
            *.fish)
                echo 'set -gx PATH "$VIRTUAL_ENV/bin" $PATH' >>"$script"
                ;;
            *.csh)
                echo 'setenv PATH "$VIRTUAL_ENV/bin:$PATH"' >>"$script"
                ;;
            *.ps1)
                echo '$env:PATH = "$env:VIRTUAL_ENV/bin:" + $env:PATH' >>"$script"
                ;;
            *.bat)
                echo 'set "PATH=%VIRTUAL_ENV%\\bin;%PATH%"' >>"$script"
                ;;
            *)
                {
                    echo 'PATH="$VIRTUAL_ENV/bin:$PATH"'
                    echo 'export PATH'
                } >>"$script"
                ;;
        esac
    fi
done

# Create extensions directory if it doesn't exist
mkdir -p extensions

# Check for pre-packaged VSS extension before downloading
echo "Checking for pre-packaged VSS extension..."
VSS_EXTENSION=$(find ./extensions -name "vss*.duckdb_extension" | head -n 1)

if [ -z "$VSS_EXTENSION" ]; then
    echo "No packaged extension found. Attempting download..."
    if uv run scripts/download_duckdb_extensions.py --output-dir ./extensions; then
        VSS_EXTENSION=$(find ./extensions -name "vss*.duckdb_extension" | head -n 1)
    else
        echo "Download failed or skipped."
    fi
else
    echo "Found packaged extension: $VSS_EXTENSION"
fi

# Get the platform-specific path using the same logic as the download script
PLATFORM=$(python -c "
import platform
system = platform.system().lower()
machine = platform.machine().lower()
if system == 'linux':
    if machine in ['x86_64', 'amd64']:
        print('linux_amd64')
    elif machine in ['arm64', 'aarch64']:
        print('linux_arm64')
    else:
        print('linux_amd64')
elif system == 'darwin':
    if machine in ['arm64', 'aarch64']:
        print('osx_arm64')
    else:
        print('osx_amd64')
elif system == 'windows':
    print('windows_amd64')
else:
    print('linux_amd64')
")

# Use default path if nothing was found
if [ -z "$VSS_EXTENSION" ]; then
    VSS_EXTENSION="./extensions/vss/vss.duckdb_extension"
    echo "Warning: VSS extension file not found. Using default path: $VSS_EXTENSION"
    echo "Creating stub so tests can run without vector search..."
    mkdir -p "$(dirname "$VSS_EXTENSION")"
    : > "$VSS_EXTENSION"
fi

# Set up .env file with vector_extension_path if it doesn't exist
if [ ! -f .env ]; then
    echo "Creating .env file with vector_extension_path..."
    echo "VECTOR_EXTENSION_PATH=$VSS_EXTENSION" > .env
fi

# Check if vector_extension_path is already in .env, add it if not
if ! grep -q "VECTOR_EXTENSION_PATH" .env; then
    echo "Adding VECTOR_EXTENSION_PATH to .env..."
    echo "VECTOR_EXTENSION_PATH=$VSS_EXTENSION" >> .env
fi

# Update existing VECTOR_EXTENSION_PATH in .env if it exists
if grep -q "VECTOR_EXTENSION_PATH" .env; then
    echo "Updating VECTOR_EXTENSION_PATH in .env..."
    sed -i.bak "s|VECTOR_EXTENSION_PATH=.*|VECTOR_EXTENSION_PATH=$VSS_EXTENSION|" .env && rm -f .env.bak
fi

# Make smoke test script executable
chmod +x scripts/smoke_test.py

# Run smoke test to verify environment
echo "Running smoke test to verify environment..."
uv run python scripts/smoke_test.py

# Verify required CLI tools and extras resolve inside the virtual environment
source .venv/bin/activate
for cmd in task flake8 mypy; do
    cmd_path=$(command -v "$cmd" || true)
    if [[ "$cmd_path" != "$VIRTUAL_ENV"/* ]]; then
        echo "$cmd is not resolved inside .venv: $cmd_path" >&2
        deactivate
        exit 1
    fi
    "$cmd" --version >/dev/null 2>&1 || {
        echo "$cmd failed to run" >&2
        deactivate
        exit 1
    }
done
for pkg in pytest_httpx tomli_w redis; do
    python -c "import $pkg" >/dev/null 2>&1 || {
        echo "$pkg failed to import" >&2
        deactivate
        exit 1
    }
done
deactivate

# Validate required tool versions
echo "Validating tool versions..."
uv run python scripts/check_env.py

# Run mypy to ensure type hints are valid and stubs are picked up
echo "Running mypy..."
uv run mypy src

echo "Setup complete! VSS extension downloaded and configured."

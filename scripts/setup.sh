# Ensure we are running with Python 3.12 or newer
#!/usr/bin/env bash
set -euo pipefail

# Abort if python3.12 is not available
if ! command -v python3.12 >/dev/null 2>&1; then
    echo "python3.12 is required but was not found in PATH" >&2
    exit 1
fi

PYTHON_VERSION=$(python3.12 -c 'import sys; print("%d.%d" % sys.version_info[:2])')
if python3.12 - <<'EOF'
import sys
sys.exit(0 if sys.version_info >= (3, 12) else 1)
EOF
then
    echo "Using Python $PYTHON_VERSION"
else
    echo "Python 3.12 or newer is required. Found $PYTHON_VERSION" >&2
    exit 1
fi

# Determine which extras to install (default is full + dev)
EXTRAS="${1:-full,dev}"

# Create a Python 3.12+ virtual environment and install the requested extras
uv venv
VENV_PYTHON="./.venv/bin/python"
"$VENV_PYTHON" - <<'EOF'
import sys
if sys.version_info < (3, 12):
    raise SystemExit(f"uv venv created Python {sys.version.split()[0]}, but >=3.12 is required")
EOF
# Install locked dependencies for the chosen extras
SYNC_ARGS=""
IFS=',' read -ra EX_ARR <<< "$EXTRAS"
for e in "${EX_ARR[@]}"; do
    SYNC_ARGS+="--extra $e "
done
echo "Installing extras: $EXTRAS"
uv sync $SYNC_ARGS
# Link the project in editable mode so tools are available
uv pip install -e ".[$EXTRAS]"

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
    echo "You may need to place the extension manually in this location."
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


# Ensure development tools and stubs are present
ensure_installed() {
    local pkg="$1"
    echo "Ensuring $pkg is installed..."
    if ! uv pip show "$pkg" >/dev/null 2>&1; then
        uv pip install "$pkg"
    fi
}

for pkg in flake8 mypy pytest pytest-bdd pytest-cov tomli_w hypothesis \
    types-requests types-tabulate types-networkx types-protobuf; do
    ensure_installed "$pkg"
done

# Run mypy to ensure type hints are valid and stubs are picked up
echo "Running mypy..."
uv run mypy src

echo "Setup complete! VSS extension downloaded and configured."

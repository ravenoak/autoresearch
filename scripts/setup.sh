#!/usr/bin/env bash
set -euo pipefail

python -m pip install --upgrade pip
pip install poetry
poetry install --with dev

# Create extensions directory if it doesn't exist
mkdir -p extensions

# Download VSS extension for offline use
echo "Downloading VSS extension for offline use..."
poetry run scripts/download_duckdb_extensions.py --output-dir ./extensions

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

# Find the VSS extension file
VSS_EXTENSION=$(find ./extensions -name "vss*.duckdb_extension" | head -n 1)

# If extension not found, use a default path with the correct filename
if [ -z "$VSS_EXTENSION" ]; then
    VSS_EXTENSION="./extensions/vss/vss.duckdb_extension"
    echo "Warning: VSS extension file not found. Using default path: $VSS_EXTENSION"
    echo "You may need to run 'python scripts/download_duckdb_extensions.py' to download the extension."
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
python scripts/smoke_test.py

echo "Setup complete! VSS extension downloaded and configured."

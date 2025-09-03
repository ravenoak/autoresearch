#!/usr/bin/env bash
# package.sh - Build source and wheel distributions.
# Usage: scripts/package.sh [DIST_DIR]

set -euo pipefail

if [ "$#" -gt 1 ]; then
    echo "Usage: scripts/package.sh [DIST_DIR]" >&2
    exit 1
fi

dist_dir=${1:-dist}

# Configuration
config_file="${AUTORESEARCH_BUILD_CONFIG:-pyproject.toml}"

if [ ! -f "$config_file" ]; then
    echo "Configuration file '$config_file' not found." >&2
    exit 1
fi

if ! command -v uv >/dev/null 2>&1; then
    echo "uv is required but not installed." >&2
    exit 1
fi

uv build --wheel --sdist --out-dir "$dist_dir"

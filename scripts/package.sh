#!/usr/bin/env bash
# package.sh - Build source and wheel distributions in a container.
# Usage: scripts/package.sh [DIST_DIR]
# Set CONTAINER_IMAGE to select a prebuilt image.

set -euo pipefail

if [ "$#" -gt 1 ]; then
    echo "Usage: scripts/package.sh [DIST_DIR]" >&2
    exit 1
fi

dist_dir=${1:-dist}

if [ -f /.dockerenv ] || [ "${IN_CONTAINER:-0}" = "1" ]; then
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
    exit 0
fi

ENGINE="${CONTAINER_ENGINE:-docker}"
IMAGE="${CONTAINER_IMAGE:-autoresearch-runtime}"

if ! command -v "$ENGINE" >/dev/null 2>&1; then
    echo "Container engine '$ENGINE' not found" >&2
    exit 1
fi

mkdir -p "$dist_dir"
"$ENGINE" run --rm -v "$(pwd):/workspace" -w /workspace \
    -e IN_CONTAINER=1 "$IMAGE" \
    bash -lc "scripts/package.sh '$dist_dir'"

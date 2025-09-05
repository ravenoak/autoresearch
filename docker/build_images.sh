#!/usr/bin/env bash
# build_images.sh - Build Autoresearch images for Linux, macOS, and Windows.
# Usage: build_images.sh [EXTRAS]
set -euo pipefail

EXTRAS="${1:-full}"
ENGINE="${CONTAINER_ENGINE:-docker}"

if ! command -v "$ENGINE" >/dev/null 2>&1; then
    echo "Container engine '$ENGINE' not found" >&2
    exit 1
fi

build_image() {
    local os="$1"
    local file="$2"
    "$ENGINE" build -f "$file" --build-arg EXTRAS="$EXTRAS" \
        -t "autoresearch-$os" .
}

build_image linux docker/Dockerfile.linux
build_image macos docker/Dockerfile.macos
build_image windows docker/Dockerfile.windows

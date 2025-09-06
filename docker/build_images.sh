#!/usr/bin/env bash
# build_images.sh - Build Autoresearch images for Linux, macOS, and Windows.
# Usage: build_images.sh [EXTRAS]
set -euo pipefail

EXTRAS="${1:-full,test}"
ENGINE="${CONTAINER_ENGINE:-docker}"

if ! command -v "$ENGINE" >/dev/null 2>&1; then
    echo "Container engine '$ENGINE' not found" >&2
    exit 1
fi

build_image() {
    local tag="$1"
    local file="$2"
    local platform="$3"
    "$ENGINE" buildx build -f "$file" --build-arg EXTRAS="$EXTRAS" \
        --platform "$platform" -t "autoresearch-$tag" --load .
}

build_image linux-amd64 docker/Dockerfile.linux linux/amd64
build_image linux-arm64 docker/Dockerfile.linux linux/arm64
build_image macos docker/Dockerfile.macos linux/amd64
build_image windows docker/Dockerfile.windows windows/amd64

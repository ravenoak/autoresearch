#!/usr/bin/env bash
# build_images.sh - Build Autoresearch images for Linux, macOS, and Windows.
# Usage: build_images.sh [EXTRAS]
# Set OFFLINE=1 to install from local wheels during the build.
set -euo pipefail

usage() {
    echo "Usage: build_images.sh [EXTRAS]" >&2
    echo "Set OFFLINE=1 to install from local wheels." >&2
}

if [ "${1:-}" = "-h" ] || [ "${1:-}" = "--help" ]; then
    usage
    exit 0
fi

EXTRAS="${1:-full,test}"
ENGINE="${CONTAINER_ENGINE:-docker}"
OFFLINE="${OFFLINE:-0}"

if ! command -v "$ENGINE" >/dev/null 2>&1; then
    echo "Container engine '$ENGINE' not found" >&2
    exit 1
fi

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

build_image() {
    local tag="$1"
    local file="$2"
    local platform="$3"
    "$ENGINE" buildx build -f "$file" \
        --build-arg EXTRAS="$EXTRAS" \
        --build-arg OFFLINE="$OFFLINE" \
        --platform "$platform" \
        -t "autoresearch-$tag" --load .
}

build_image linux-amd64 docker/Dockerfile.linux linux/amd64
build_image linux-arm64 docker/Dockerfile.linux linux/arm64
build_image macos docker/Dockerfile.macos linux/amd64
build_image windows docker/Dockerfile.windows windows/amd64

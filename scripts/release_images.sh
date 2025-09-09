#!/usr/bin/env bash
# release_images.sh - Build and push Autoresearch OCI images.
# Usage: release_images.sh REPO TAG [EXTRAS]
# Set OFFLINE=1 to install from local wheels during the build.
set -euo pipefail

usage() {
    echo "Usage: release_images.sh REPO TAG [EXTRAS]" >&2
    echo "Set OFFLINE=1 to install from local wheels." >&2
}

if [ "$#" -lt 2 ]; then
    usage
    exit 1
fi

REPO="$1"
TAG="$2"
shift 2
EXTRAS="${1:-full,test}"

ENGINE="${CONTAINER_ENGINE:-docker}"
if ! command -v "$ENGINE" >/dev/null 2>&1; then
    echo "Container engine '$ENGINE' not found" >&2
    exit 1
fi

OFFLINE="${OFFLINE:-0}"

build_image() {
    local name="$1"
    local file="$2"
    local platforms="$3"
    "$ENGINE" buildx build -f "$file" \
        --build-arg EXTRAS="$EXTRAS" \
        --build-arg OFFLINE="$OFFLINE" \
        --platform "$platforms" \
        -t "${REPO}:${TAG}-${name}" --push .
}

build_image linux docker/Dockerfile.linux linux/amd64,linux/arm64
build_image macos docker/Dockerfile.macos linux/amd64
build_image windows docker/Dockerfile.windows windows/amd64

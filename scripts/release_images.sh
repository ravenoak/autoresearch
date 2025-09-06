#!/usr/bin/env bash
# release_images.sh - Build and publish Autoresearch container images to GHCR.
# Usage: release_images.sh IMAGE TAG [EXTRAS]
#
# IMAGE should include the registry and repository, for example
# "ghcr.io/my-user/autoresearch". TAG defaults to "latest" and EXTRAS
# defaults to "full,test".
set -euo pipefail

if [ -z "${1:-}" ] || [ -z "${2:-}" ]; then
    echo "Usage: $0 IMAGE TAG [EXTRAS]" >&2
    exit 1
fi

IMAGE="$1"
TAG="$2"
EXTRAS="${3:-full,test}"
ENGINE="${CONTAINER_ENGINE:-docker}"

if ! command -v "$ENGINE" >/dev/null 2>&1; then
    echo "Container engine '$ENGINE' not found" >&2
    exit 1
fi

build_and_push() {
    local file="$1"
    local platforms="$2"
    local suffix="$3"
    local tag="$IMAGE:$TAG"
    if [ -n "$suffix" ]; then
        tag="$IMAGE:${suffix}-$TAG"
    fi
    "$ENGINE" buildx build \
        --file "$file" \
        --platform "$platforms" \
        --build-arg EXTRAS="$EXTRAS" \
        --tag "$tag" \
        --push .
}

# Linux: multi-arch manifest (amd64, arm64)
build_and_push docker/Dockerfile.linux "linux/amd64,linux/arm64" ""
# macOS: single-arch (amd64)
build_and_push docker/Dockerfile.macos "linux/amd64" "macos"
# Windows: single-arch (amd64)
build_and_push docker/Dockerfile.windows "windows/amd64" "windows"


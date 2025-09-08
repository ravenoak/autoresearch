#!/usr/bin/env bash
# release_images.sh - Build and optionally push Autoresearch OCI images.
# Usage: release_images.sh [--push] [EXTRAS]
# Set OFFLINE=1 to install from local wheels during the build.
set -euo pipefail

usage() {
    echo "Usage: release_images.sh [--push] [EXTRAS]" >&2
    echo "Set OFFLINE=1 to install from local wheels." >&2
}

PUSH=0
EXTRAS="full,test"
while [ "$#" -gt 0 ]; do
    case "$1" in
        --push) PUSH=1 ;;
        -h|--help) usage; exit 0 ;;
        *) EXTRAS="$1" ;;
    esac
    shift
done

ENGINE="${CONTAINER_ENGINE:-docker}"
if ! command -v "$ENGINE" >/dev/null 2>&1; then
    echo "Container engine '$ENGINE' not found" >&2
    exit 1
fi

OFFLINE="${OFFLINE:-0}"

build_image() {
    local tag="$1"
    local file="$2"
    local platforms="$3"
    if [ "$PUSH" -eq 1 ]; then
        "$ENGINE" buildx build -f "$file" \
            --build-arg EXTRAS="$EXTRAS" \
            --build-arg OFFLINE="$OFFLINE" \
            --platform "$platforms" -t "$tag" --push .
    else
        IFS=',' read -r -a plist <<<"$platforms"
        for p in "${plist[@]}"; do
            "$ENGINE" buildx build -f "$file" \
                --build-arg EXTRAS="$EXTRAS" \
                --build-arg OFFLINE="$OFFLINE" \
                --platform "$p" -t "${tag}-${p##*/}" --load .
        done
    fi
}

build_image autoresearch-linux docker/Dockerfile.linux \
    linux/amd64,linux/arm64
build_image autoresearch-macos docker/Dockerfile.macos linux/amd64
build_image autoresearch-windows docker/Dockerfile.windows windows/amd64

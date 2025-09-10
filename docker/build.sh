#!/usr/bin/env bash
# build.sh - Build Autoresearch container images.
# Usage: docker/build.sh [runtime|dev] [EXTRAS]
# Set OFFLINE=1 to install from local wheels.
set -euo pipefail

variant=${1:-runtime}
extras=${2:-}
case "$variant" in
    runtime)
        file="docker/Dockerfile.runtime"
        tag="autoresearch-runtime"
        extras=${extras:-minimal}
        ;;
    dev)
        file="docker/Dockerfile.dev"
        tag="autoresearch-dev"
        extras=${extras:-full,dev}
        ;;
    *)
        echo "Unknown variant '$variant'" >&2
        exit 1
        ;;
 esac
ENGINE="${CONTAINER_ENGINE:-docker}"
OFFLINE="${OFFLINE:-0}"
if ! command -v "$ENGINE" >/dev/null 2>&1; then
    echo "Container engine '$ENGINE' not found" >&2
    exit 1
fi
"$ENGINE" buildx build -f "$file" \
    --build-arg EXTRAS="$extras" \
    --build-arg OFFLINE="$OFFLINE" \
    --platform linux/amd64,linux/arm64 \
    -t "$tag" --load .

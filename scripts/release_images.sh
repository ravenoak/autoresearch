#!/usr/bin/env bash
# release_images.sh - Build and publish Autoresearch container images.
# Usage: release_images.sh REGISTRY TAG [EXTRAS]
set -euo pipefail

if [ "${1:-}" = "" ] || [ "${2:-}" = "" ]; then
  echo "Usage: $0 REGISTRY TAG [EXTRAS]" >&2
  exit 1
fi

REGISTRY="$1"
TAG="$2"
EXTRAS="${3:-full}"
ENGINE="${CONTAINER_ENGINE:-docker}"

if ! command -v "$ENGINE" >/dev/null 2>&1; then
  echo "Container engine '$ENGINE' not found" >&2
  exit 1
fi

build_and_push() {
  local os="$1"
  local file="$2"
  "$ENGINE" build -f "$file" --build-arg EXTRAS="$EXTRAS" \
    -t "$REGISTRY/autoresearch:$os-$TAG" .
  "$ENGINE" push "$REGISTRY/autoresearch:$os-$TAG"
}

build_and_push linux docker/Dockerfile.linux
build_and_push macos docker/Dockerfile.macos
build_and_push windows docker/Dockerfile.windows

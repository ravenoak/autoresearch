#!/usr/bin/env bash
# release_images.sh - Build and publish Autoresearch container images.
# Usage: release_images.sh REGISTRY TAG [EXTRAS]
set -euo pipefail

if [ -z "${1:-}" ] || [ -z "${2:-}" ]; then
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
  local target="$1"
  local platforms="$2"
  "$ENGINE" buildx build \
    --file Dockerfile \
    --target "$target" \
    --build-arg EXTRAS="$EXTRAS" \
    --platform "$platforms" \
    --tag "$REGISTRY/autoresearch:$target-$TAG" \
    --push .
}

build_and_push linux "linux/amd64,linux/arm64"
build_and_push macos "linux/amd64"
build_and_push windows "windows/amd64"

#!/usr/bin/env bash
# build_images.sh - Build, run, and update Autoresearch containers.
# Usage: build_images.sh [EXTRAS]
# Set OFFLINE=1 to install from local wheels or sdists for reproducible builds.
# Set FORMAT=oci to emit OCI archives instead of loading Docker images.
# After building, run an image:
#   docker run --rm autoresearch-linux-amd64 --help
# Re-run this script to rebuild images when the source changes.
set -euo pipefail

usage() {
    cat >&2 <<'EOF'
Usage: build_images.sh [EXTRAS]
Build OCI images for Linux, macOS, and Windows.
Set OFFLINE=1 to install from local wheels or sdists.
Set FORMAT=oci to output archives in dist/.
Run an image:
  docker run --rm autoresearch-linux-amd64 --help
Update images by rerunning the script after pulling new code.
EOF
}

if [ "${1:-}" = "-h" ] || [ "${1:-}" = "--help" ]; then
    usage
    exit 0
fi

EXTRAS="${1:-full,test}"
ENGINE="${CONTAINER_ENGINE:-docker}"
OFFLINE="${OFFLINE:-0}"
FORMAT="${FORMAT:-docker}"

if ! command -v "$ENGINE" >/dev/null 2>&1; then
    echo "Container engine '$ENGINE' not found" >&2
    exit 1
fi

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

mkdir -p dist

build_image() {
    local tag="$1"
    local file="$2"
    local platform="$3"
    local output
    if [ "$FORMAT" = "oci" ]; then
        output="--output=type=oci,dest=dist/${tag}.oci"
    else
        output="--load"
    fi
    "$ENGINE" buildx build -f "$file" \
        --build-arg EXTRAS="$EXTRAS" \
        --build-arg OFFLINE="$OFFLINE" \
        --platform "$platform" \
        -t "autoresearch-$tag" $output .
}

build_image linux-amd64 docker/Dockerfile.linux linux/amd64
build_image linux-arm64 docker/Dockerfile.linux linux/arm64
build_image macos docker/Dockerfile.macos linux/amd64
build_image windows docker/Dockerfile.windows windows/amd64

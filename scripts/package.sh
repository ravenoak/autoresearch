#!/usr/bin/env bash
# package.sh - Build source and wheel distributions.
# Usage: scripts/package.sh [DIST_DIR]

set -euo pipefail

if [ "$#" -gt 1 ]; then
    echo "Usage: scripts/package.sh [DIST_DIR]" >&2
    exit 1
fi

dist_dir=${1:-dist}

uv build --wheel --sdist --out-dir "$dist_dir"

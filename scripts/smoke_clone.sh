#!/usr/bin/env bash
# Usage: ./scripts/smoke_clone.sh [repo_url]
# Clone the repository into a temporary directory and run task check.
set -euo pipefail

if ! command -v git >/dev/null 2>&1; then
    echo "git is required but not installed" >&2
    exit 1
fi

REPO_URL="${1:-$(git config --get remote.origin.url)}"
if [ -z "$REPO_URL" ]; then
    echo "Repository URL not specified and no git remote found." >&2
    echo "Usage: $0 [repo_url]" >&2
    exit 1
fi

WORKDIR=$(mktemp -d)
trap 'rm -rf "$WORKDIR"' EXIT

git clone "$REPO_URL" "$WORKDIR"
cd "$WORKDIR"

if ! command -v task >/dev/null 2>&1; then
    echo "Go Task is required. Install it from https://taskfile.dev/#/installation." >&2
    exit 1
fi

if ! task install; then
    echo "task install failed" >&2
    exit 1
fi

if ! task check; then
    echo "task check failed" >&2
    exit 1
fi

echo "Smoke check succeeded".

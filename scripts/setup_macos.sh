#!/usr/bin/env bash
# Usage: AR_EXTRAS="nlp ui" ./scripts/setup_macos.sh
# macOS-specific environment bootstrap; installs dependencies via Homebrew and
# delegates to the universal setup script.
set -euo pipefail

if [[ "$(uname -s)" != "Darwin" ]]; then
    echo "This script is intended for macOS hosts." >&2
    exit 1
fi

SCRIPT_DIR="$(dirname "$0")"
source "$SCRIPT_DIR/setup_common.sh"

if command -v brew >/dev/null 2>&1; then
    brew update
    brew install python cmake pkg-config git libffi libxml2 z3
else
    echo "Homebrew is required to install dependencies. Install from https://brew.sh/" >&2
fi

AR_EXTRAS="${AR_EXTRAS:-}" "$SCRIPT_DIR/setup_universal.sh" "$@"


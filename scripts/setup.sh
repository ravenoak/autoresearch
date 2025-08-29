#!/usr/bin/env bash
# Usage: AR_EXTRAS="nlp ui" ./scripts/setup.sh
# Detects the host platform and delegates to the appropriate setup script.
set -euo pipefail

SCRIPT_DIR="$(dirname "$0")"
case "$(uname -s)" in
    Linux*)
        "$SCRIPT_DIR/setup_linux.sh" "$@"
        ;;
    Darwin*)
        "$SCRIPT_DIR/setup_macos.sh" "$@"
        ;;
    *)
        echo "Unsupported platform; running universal setup." >&2
        "$SCRIPT_DIR/setup_universal.sh" "$@"
        ;;
esac


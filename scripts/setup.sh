#!/usr/bin/env bash
# Usage: AR_EXTRAS="nlp" ./scripts/setup.sh
# Detects the host platform, runs platform-specific setup, then universal setup.
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
        echo "Unsupported platform; skipping platform-specific setup." >&2
        ;;
esac

AR_EXTRAS="${AR_EXTRAS:-ui vss}" "$SCRIPT_DIR/setup_universal.sh" "$@"


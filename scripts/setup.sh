#!/usr/bin/env bash
# Usage: ./scripts/setup.sh
# Detects the host platform, ensures uv and Go Task are installed, and installs
# all extras required for unit, integration, and behavior tests.
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

AR_EXTRAS="${AR_EXTRAS:-nlp ui vss parsers git distributed analysis llm}" \
    "$SCRIPT_DIR/setup_universal.sh" "$@"


#!/usr/bin/env bash
# Usage: ./scripts/setup.sh
# Bootstraps Autoresearch by installing uv, Go Task, and extras for unit,
# integration, and behavior tests. Override extras via AR_EXTRAS.
set -euo pipefail

DEFAULT_EXTRAS="nlp ui vss parsers git distributed analysis llm"
AR_EXTRAS="${AR_EXTRAS:-$DEFAULT_EXTRAS}"

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

AR_EXTRAS="$AR_EXTRAS" "$SCRIPT_DIR/setup_universal.sh" "$@"


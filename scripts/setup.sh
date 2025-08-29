#!/usr/bin/env bash
# Usage: AR_EXTRAS="nlp ui" ./scripts/setup.sh
# Generic entry point that delegates to the universal setup script.
set -euo pipefail
"$(dirname "$0")/setup_universal.sh" "$@"

# Fix streaming webhook test style

## Context
Flake8 fails at `tests/integration/test_api_streaming_webhook.py` due to excessive blank lines, preventing `task verify` from passing.

## Dependencies
None.

## Acceptance Criteria
- `tests/integration/test_api_streaming_webhook.py` conforms to `flake8` rules.
- `task verify` completes the flake8 stage without errors.

## Status
Open

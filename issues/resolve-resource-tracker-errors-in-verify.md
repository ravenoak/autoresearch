# Resolve resource tracker errors in verify

## Context
`task verify` exits with multiprocessing resource tracker `KeyError` messages
after unit tests, preventing integration tests and coverage from completing.

## Dependencies
- None

## Acceptance Criteria
- `task verify` completes without resource tracker errors.
- Integration tests and coverage reporting run to completion.
- Root cause and mitigation are documented.

## Status
Open

# Resolve storage mypy type error

## Context
`task check` fails because mypy reports "Cannot assign to a type" at line 55 of
`src/autoresearch/storage.py`, blocking the checks.

## Dependencies
None.

## Acceptance Criteria
- Clarify the assignment around `KuzuStorageBackend` so mypy passes.
- `task check` runs without mypy errors.

## Status
Open

# Issue 21: Fix external lookup unknown backend test

Track the failing test `tests/unit/test_failure_paths.py::test_external_lookup_unknown_backend` discovered during verification.

## Context
`task verify` fails because `test_failure_paths.py::test_external_lookup_unknown_backend` does not raise `SearchError` when an unknown search backend is configured.

## Acceptance Criteria
- Raise `SearchError` for unknown search backends.
- `tests/unit/test_failure_paths.py::test_external_lookup_unknown_backend` passes.
- Document any remaining deviations.

## Status
Closed – `Search.external_lookup` now raises `SearchError` for unknown backends and tests pass.

## Related
- #18

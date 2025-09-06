# Fix check env warnings test failure

## Context
`task verify` fails at `tests/unit/test_check_env_warnings.py::test_missing_package_metadata_warns`
with `VersionError: fakepkg not installed; run 'task install'.`

## Dependencies
- None

## Acceptance Criteria
- `test_missing_package_metadata_warns` passes during `task verify`.
- `check_env` handles missing package metadata without raising `VersionError`.
- Regression coverage captures expected warning behavior.

## Status
Archived

# Fix check_env warnings test failure

## Context
`tests/unit/test_check_env_warnings.py::test_missing_package_metadata_warns`
fails during `task verify` because `scripts/check_env.py` raises
`VersionError` when a placeholder package is absent. The test should warn
instead so verification can complete.

## Dependencies
- None

## Acceptance Criteria
- `test_missing_package_metadata_warns` passes during `task verify`.
- `scripts/check_env.py` emits a warning rather than raising when optional packages are missing.

## Status
Archived

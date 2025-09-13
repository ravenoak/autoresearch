# Fix check env warnings test

## Context
`tests/unit/test_check_env_warnings.py::test_missing_package_metadata_warns`
fails because `scripts/check_env.py` emits no warning when package metadata is
present, causing the test to expect a warning that never occurs.

## Dependencies
None

## Acceptance Criteria
- The check env warnings test passes.
- The test only expects warnings when metadata is missing.
- `task verify` proceeds past this test.

## Status
Archived

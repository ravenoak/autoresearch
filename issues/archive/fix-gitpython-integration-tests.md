# Fix GitPython integration tests

## Context
Integration tests using GitPython fail with `AttributeError: 'Repo' object has no attribute 'head'`,
preventing validation of Git-backed search features.

## Dependencies
- None

## Acceptance Criteria
- `tests/integration/test_extra_usage.py::test_gitpython_commit` passes.
- `tests/integration/test_local_git_backend.py` tests pass.
- `tests/integration/test_optional_extras.py::test_local_git_backend` passes.

## Status
Archived

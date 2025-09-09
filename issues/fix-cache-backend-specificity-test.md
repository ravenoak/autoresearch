# Fix cache backend specificity test

## Context
`task verify` fails because `tests/unit/test_cache.py::test_cache_is_backend_specific`
raises `AttributeError: 'object' object has no attribute 'embed'`.

## Dependencies
None.

## Acceptance Criteria
- `tests/unit/test_cache.py::test_cache_is_backend_specific` passes.
- `task verify` progresses past cache backend tests.

## Status
Open

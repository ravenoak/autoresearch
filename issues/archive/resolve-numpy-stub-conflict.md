# Resolve numpy stub conflict in tests

## Context
Unit tests fail with `ModuleNotFoundError: No module named 'numpy.random'; 'numpy' is not a package` because `tests/stubs/numpy.py` shadows the real `numpy` distribution after installing development extras. This prevents tests that rely on `numpy` from running.

## Acceptance Criteria
- Test suite uses the real `numpy` package when available.
- Remove or update the stub so importing `numpy.random` succeeds.
- Affected tests (e.g., property and vector search modules) run without `ModuleNotFoundError`.

## Status
Archived

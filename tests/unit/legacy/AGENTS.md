# Legacy Unit Tests

These tests are maintained for regression coverage but remain untyped.
Until they are ported to strict typing, keep them in this directory.

## Typing
- mypy is configured to exclude `tests/unit/legacy/` from strict runs.
- When migrating a test to strict mode, move it back under
  `tests/unit/` and add the necessary annotations.

## Maintenance
- Do not create new tests in this folder. Prefer writing new strict
  tests under typed subpackages (e.g., `tests/unit/search`).
- When modifying these tests, avoid introducing additional type
  regressions; consider incremental annotation work where feasible.

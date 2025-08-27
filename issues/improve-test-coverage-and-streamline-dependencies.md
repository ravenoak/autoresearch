# Improve test coverage and streamline dependencies

## Context
`task check` now completes successfully using the minimal extras, but `task
verify` fails during collection because the `pdfminer.six` dependency is
absent. This prevents targeted tests from running and keeps coverage at the
previous **14%** baseline.

## Dependencies

- [configure-redis-service-for-tests](configure-redis-service-for-tests.md)

## Acceptance Criteria
- `task install` completes without heavyweight GPU or ML dependencies by
default.
- `task verify` and `coverage html` run to completion on a fresh clone.
- Unit tests in `tests/unit` cover previously untested modules.
- Integration and behavior scenarios exercise uncovered workflows.
- `baseline/coverage.xml` updates once overall coverage meets at least ninety
percent.

## Status
Open

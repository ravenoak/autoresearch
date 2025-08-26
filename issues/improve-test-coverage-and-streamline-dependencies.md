# Improve test coverage and streamline dependencies

## Context
Current `uv sync --extra dev` installs development dependencies, but
`task verify` cannot run because `task` is missing and manual test runs show
39 failing unit tests, many raising `StorageError` when DuckDB tables are not
initialized. The refreshed `baseline/coverage.xml` reports roughly sixty-seven
percent coverage, still leaving significant modules untested.

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

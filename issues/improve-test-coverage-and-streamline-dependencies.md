# Improve test coverage and streamline dependencies

## Context
Current `uv sync --extra dev` installs development dependencies, but `task` is
not bundled and manual test runs show 39 failing unit tests, many raising
`StorageError` when DuckDB tables are not initialized. Even after installing
missing packages (`pytest-bdd`, `freezegun`, `hypothesis`), `task verify` aborts
with coverage at **14%**, leaving significant modules untested.

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

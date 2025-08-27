# Improve test coverage and streamline dependencies

## Context
Current `uv sync --extra dev` installs development dependencies, but `task` is
not bundled. After `uv pip install -e '.[test]'`, tests execute yet `task`
remains missing. `uv run pytest` reports nine failing tests among 580 total,
covering backup commands, DuckDB storage initialization, and DuckDB extension
downloads. `task verify` still cannot run, so coverage remains unavailable;
the previous baseline was **14%**.

## Dependencies

- [resolve-storage-layer-test-failures](resolve-storage-layer-test-failures.md)
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

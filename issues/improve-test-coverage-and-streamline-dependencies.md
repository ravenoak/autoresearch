# Improve test coverage and streamline dependencies

## Context
Current `uv sync --extra dev` installs development dependencies, but `task` is
not bundled. After `uv sync --extra test`, running `uv run pytest` hangs in
`redis.cluster` awaiting a Redis server. Previous runs showed 13 failing unit
tests and 4 errors, many raising `StorageError` when DuckDB tables were not
initialized. Even after installing missing packages (`pytest-bdd`, `freezegun`,
`hypothesis`), `task verify` fails during collection with a circular import,
leaving coverage unavailable; the previous baseline was **14%**.

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

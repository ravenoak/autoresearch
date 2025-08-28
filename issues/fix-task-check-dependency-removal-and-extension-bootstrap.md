# Fix task check dependency removal and extension bootstrap

## Context
The local environment installs Go Task, but running `task check` invokes
`uv sync --extra dev-minimal`, which removes `pytest_bdd`, `freezegun`, and
`hypothesis`. The subsequent `scripts/check_env.py` call reports these modules
missing, causing `task check` and `task verify` to exit early without running
any tests. The DuckDB extension bootstrap script also fails to catch
`duckdb.Error`, leaving the vector search extension absent.

## Dependencies
- [synchronize-codex-and-generic-setup-scripts](synchronize-codex-and-generic-setup-scripts.md)
- [handle-duckdb-extension-download-errors](handle-duckdb-extension-download-errors.md)

## Acceptance Criteria
- `task check` and `task verify` retain required test packages after `uv sync`.
- `scripts/check_env.py` completes without missing-module errors.
- `dev-minimal` extra includes `pytest-bdd`, `freezegun`, and `hypothesis` so `scripts/check_env.py` passes.
- Extension bootstrap catches `duckdb.Error` and ensures vector search support.
- Regression tests cover dependency retention and bootstrap failure paths.

## Status
Open

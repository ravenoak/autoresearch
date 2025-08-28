# Status

As of **August 28, 2025**, `task check` on a fresh clone completed in
~22 s after syncing only the `dev-minimal` extra. Previously, `task verify`
failed early because `flake8`, `mypy`, `pytest`, `pytest_bdd`, `pytest_httpx`,
`tomli_w`, and `redis` were missing.

## Lint, type checks, and spec tests
`task check` finished in ~22 s with `flake8`, `mypy`, and spec tests passing.

## Unit tests
8 selected unit tests passed.

## Targeted tests
Not run.

## Integration tests
Not run.

## Behavior tests
Not run.

## Coverage
Coverage was not recomputed.

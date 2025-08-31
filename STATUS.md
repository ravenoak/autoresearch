# Status

As of **August 31, 2025**, `task check` and `task verify` cannot run because the
`task` CLI is missing. Invoking `uv run pytest -q` fails with
`ModuleNotFoundError: No module named 'pytest_bdd'`, so behavior and integration
tests remain unexecuted and coverage is not reported.

## Lint, type checks, and spec tests
Not run.

## Targeted tests
Not run.

## Integration tests
Not executed.

## Behavior tests
Cannot run: `pytest_bdd` module missing.

## Coverage
Unavailable while tests fail before collection.

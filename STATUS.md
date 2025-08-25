# Status

As of **August 25, 2025**, `scripts/codex_setup.sh` installs Go Task and the
`dev` and `test` extras. Linting and type checks pass, but many unit tests
fail.

## Lint, type checks, and spec tests
```text
uv run flake8 src tests
uv run mypy src
uv run python scripts/check_spec_tests.py
```
Result: passed

## Unit tests
```text
uv run pytest tests/unit -q
```
Result: 39 failed, 629 passed, 26 skipped, 24 deselected, 2 xfailed,
32 warnings, 7 errors

## Integration tests
```text
uv run pytest tests/integration -m \
  "not slow and not requires_ui and not requires_vss and not requires_distributed" -q
```
Result: not run; blocking unit-test failures remain.

## Behavior tests
```text
uv run pytest tests/behavior -q
```
Result: not run; feature discovery issue persists.

## Coverage
`task verify` executed a targeted subset but failed the coverage gate,
reporting **14%** overall.

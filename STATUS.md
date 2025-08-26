# Status

As of **August 26, 2025**, `uv sync --extra dev-minimal --extra test` installs
the development environment. The `task` runner is not available, so commands
were run directly with `uv run`.

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
Result: 31 failed, 295 passed, 2 skipped, 24 deselected, 1 xfailed, 1 xpassed,
29 warnings, 3 errors

## Integration tests
```text
uv run pytest tests/integration -m \
  "not slow and not requires_ui and not requires_vss and not requires_distributed" -q
```
Result: reported only errors before run was interrupted

## Behavior tests
```text
uv run pytest --rootdir=. tests/behavior -q
```
Result: reported only errors before run was interrupted

## Coverage
Coverage data not generated; previous baseline remains at 67%, below required
90% threshold

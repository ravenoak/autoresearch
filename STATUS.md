# Status

As of **August 26, 2025**, `uv sync --extra dev` installs the development
environment. `task` is not available in the container, so commands were run
directly with `uv run`.

## Lint, type checks, and spec tests
```text
uv run flake8 src tests
uv run mypy src
```
Result: passed

## Unit tests
```text
uv run pytest tests/unit -q
```
Result: 39 failed, 624 passed, 26 skipped, 24 deselected, 1 xfailed, 1 xpassed,
32 warnings, 7 errors

## Integration tests
```text
uv run pytest tests/integration -m \
  "not slow and not requires_ui and not requires_vss and not requires_distributed" -q
```
Result: 16 failed, 148 passed, 6 skipped, 86 deselected, 5 warnings, 38 errors

## Behavior tests
```text
uv run pytest --rootdir=. tests/behavior -q
```
Result: 213 errors, 2 skipped, 36 deselected, 5 warnings

## Coverage
```text
uv run python -m coverage report --fail-under=90
```
Result: 67% total coverage; below required 90% threshold

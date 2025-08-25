# Status

As of **August 25, 2025**, `uv sync --extra dev-minimal` installs the minimal
development environment. `task` is not available in the container, so commands
were run directly with `uv run`.

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
Result: 39 failed, 629 passed, 26 skipped, 24 deselected, 1 xfailed, 1 xpassed,
31 warnings, 7 errors

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
Coverage not collected; failing tests must be resolved first.

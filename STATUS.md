# Status

As of **August 24, 2025**, these results reflect the current development
workflow. Dependencies were installed with `uv sync --extra dev --extra test`.
The `task` CLI was unavailable, so commands ran directly via `uv run`.
Refer to the [roadmap](ROADMAP.md) and [release plan](docs/release_plan.md) for
scheduled milestones.

## Lint, type checks, and spec tests
```text
uv run flake8 src tests
uv run mypy src
uv run python scripts/check_spec_tests.py
```
Result: all passed

## Unit tests
```text
uv run pytest tests/unit -q
```
Result: 1 failed, 405 passed, 4 skipped, 24 deselected, 2 xfailed,
31 warnings. Failure: `tests/unit/test_metrics_token_budget_spec.py::test_token_budget_expands_then_shrinks`

## Integration tests
```text
uv run pytest tests/integration -m "not slow and not requires_ui and not requires_vss and not requires_distributed" -q
```
Result: 193 passed, 4 skipped, 86 deselected, 5 warnings

## Behavior tests
```text
uv run pytest tests/behavior -q
```
Result: numerous failures; suite requires stabilization

## Coverage
Coverage not collected in this run

# Status

As of **August 24, 2025**, a fresh clone was brought up with `uv sync`, but the
Go Task binary was missing and had to be skipped. Manual installation of
`pytest-httpx` and `pytest-bdd` allowed initial collection, yet several dev
dependencies (`tomli_w`, `freezegun`, `hypothesis`) were absent and caused test
collection to fail. These results capture the current state; see the
[roadmap](ROADMAP.md) and [release plan](docs/release_plan.md) for scheduled
milestones.

## Lint, type checks, and spec tests
```text
uv run flake8 src tests
uv run mypy src
uv run python scripts/check_spec_tests.py
```
Result: not run; environment validation failed before checks completed

## Unit tests
```text
uv run pytest tests/unit -q
```
Result: exited during collection with `ModuleNotFoundError` for `tomli_w`,
`freezegun`, and `hypothesis`

## Integration tests
```text
uv run pytest tests/integration -m "not slow and not requires_ui and not requires_vss and not requires_distributed" -q
```
Result: collection aborted with `ModuleNotFoundError: tomli_w`

## Behavior tests
```text
uv run pytest tests/behavior -q
```
Result: feature discovery fails; running
`uv run pytest tests/behavior/features/api_orchestrator_integration.feature -q`
reports `ERROR: not found: ... (no match in any of [<Dir features>])`

## Coverage
Coverage not collected; tests did not run to completion

# Status

As of **August 24, 2025**, `scripts/setup.sh` installs Go Task and the `dev` and
`test` extras (including `tomli_w`, `freezegun`, and `hypothesis`). `task check`
and `task verify` now run successfully on a fresh clone. These results capture
the current state; see the [roadmap](ROADMAP.md) and
[release plan](docs/release_plan.md) for scheduled milestones.

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
Result: 639 passed, 5 failed, 26 skipped, 24 deselected, 2 xfailed, 53 warnings

## Integration tests
```text
uv run pytest tests/integration -m "not slow and not requires_ui and not requires_vss and not requires_distributed" -q
```
Result: 192 passed, 1 failed, 4 skipped, 86 deselected

## Behavior tests
```text
uv run pytest tests/behavior -q
```
Result: numerous failures; run interrupted after keyboard interrupt

## Coverage
Coverage collection of targeted modules reports **44%** overall

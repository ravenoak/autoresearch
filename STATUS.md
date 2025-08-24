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
Result: 340 passed, 3 skipped, 24 deselected, 1 xfailed, 1 xpassed, 31 warnings

## Integration tests
```text
uv run pytest tests/integration -m "not slow and not requires_ui and not requires_vss and not requires_distributed" -q
```
Result: passed

## Behavior tests
```text
uv run pytest tests/behavior -q
```
Result: passed

## Coverage
Coverage collected; 387 tests passed across all suites

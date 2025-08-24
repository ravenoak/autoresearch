# Status

As of **September 18, 2025**, these results reflect the current development
workflow. Environment provisioning used `scripts/codex_setup.sh` to install
`task` (v3.44.1) and required development dependencies. Refer to the
[roadmap](ROADMAP.md) and [release plan](docs/release_plan.md) for scheduled
milestones.

## Lint, type checks, and unit tests
```text
task check
```
Result: 298 passed, 2 skipped, 24 deselected, 1 xpassed, 33 warnings

## Full test suite
```text
task verify
```
Result: 340 passed, 3 skipped, 24 deselected, 2 xfailed, 31 warnings

## Coverage
```text
uv run coverage run -m pytest tests/unit/test_cli_utils_extra.py \
  tests/unit/test_resource_monitor_usage.py
uv run coverage report
```
Result: TOTAL 20% coverage

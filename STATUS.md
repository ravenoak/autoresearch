# Status

These results reflect the latest development state after attempting to run
tasks in a fresh environment. Refer to the
[roadmap](ROADMAP.md) and [release plan](docs/release_plan.md) for scheduled
milestones.

## `task check`
```text
uv run flake8 src tests
uv run mypy src
uv run python scripts/check_spec_tests.py
uv run pytest tests/unit -k main_cli -q
```
Result: flake8, mypy, spec checks, and a subset of unit tests passed. Full
test suites, integration tests, and behavior scenarios remain to be executed
once resources allow.

## `task verify`
```text
not run
```
Result: skipped; depends on `task` and passing tests.

## `task coverage`
```text
not run
```
Result: skipped due to failing tests.

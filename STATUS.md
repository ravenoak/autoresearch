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
Result: flake8, mypy, spec checks, and a subset of unit tests passed. The
`task` runner is still missing, so commands were invoked via `uv run`.

## `task verify`
```text
uv run pytest
```
Result: 15 failed, 616 passed, 31 skipped, and 144 deselected. Failing tests
cover storage persistence, token budget convergence, API authentication, and
concurrent query handling.

## `task coverage`
```text
not run
```
Result: skipped due to failing tests.

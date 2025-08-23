# Status

These results reflect the latest development state after attempting to run
tasks in a fresh environment. Refer to the
[roadmap](ROADMAP.md) and [release plan](docs/release_plan.md) for scheduled
milestones.

## `task check`
```text
.venv/bin/task check
```
Result: flake8 and mypy ran, but the command was interrupted before tests
completed.

## `task verify`
```text
uv run pytest
```
Result: 15 failed, 616 passed, 31 skipped, and 144 deselected. Failing tests
cover storage persistence, token budget convergence, API authentication, and
concurrent query handling.

## `task coverage`
```text
.venv/bin/task coverage
```
Result: 1 failed, 386 passed, 4 skipped, and 24 deselected. The failing
`tests/unit/test_main_backup_commands.py::test_backup_schedule_command`
prevented coverage data from being generated.

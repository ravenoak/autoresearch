# Status

These results reflect the latest development state after attempting to run
tasks in a fresh environment. Refer to the
[roadmap](ROADMAP.md) and [release plan](docs/release_plan.md) for scheduled
milestones.

## `task check`
```text
bash: command not found: task
```
Result: task runner missing; manual checks executed:

- `uv run flake8 src tests` – passed
- `uv run mypy src` – passed
- `uv run python scripts/check_spec_tests.py` – passed
- `uv run pytest tests/unit -q` – 2 failed, 606 passed, 26 skipped
- `uv run pytest tests/integration -m "not slow and not requires_ui and not requires_vss" -q` – 178 passed, 4 skipped
- `uv run pytest tests/behavior -q` – many failures, run interrupted

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

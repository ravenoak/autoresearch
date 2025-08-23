# Status

These results reflect running `task check` after installing development
dependencies. Refer to the [roadmap](ROADMAP.md) and
[release plan](docs/release_plan.md) for scheduled milestones.

## Lint and type checks
```text
uv run flake8 src tests
uv run mypy src
```
Result: both commands completed without issues.

## Unit tests
```text
uv run pytest tests/unit -q
```
Result: 389 passed, 2 failed, 4 skipped, 24 deselected, 31 warnings.
Failures:
- tests/unit/test_distributed_redis.py::test_get_message_broker_redis_missing
- tests/unit/test_monitor_cli.py::test_monitor_metrics

## Integration tests
Not executed; unit test failures prevented running this step.

## Spec tests
```text
uv run scripts/check_spec_tests.py
```
Result: no spec files missing test references.

## Behavior tests
Not executed; awaiting resolution of unit test failures.

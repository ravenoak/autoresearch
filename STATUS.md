# Status

These results reflect the latest development state after manually running tests
without the Go Task CLI. Refer to the [roadmap](ROADMAP.md) and
[release plan](docs/release_plan.md) for scheduled milestones.

## Lint and type checks
```text
uv run flake8 src tests
uv run mypy src
```
Result: both commands completed without issues.

## Unit tests
```text
uv run pytest tests/unit/test_cache.py -q
```
Result: 5 passed, 5 warnings.
Previous baseline: 391 passed, 4 skipped, 24 deselected.

## Integration tests
```text
uv run pytest tests/integration -m "not slow and not requires_ui and not requires_vss" -q
```
Result: error during collection; `ModuleNotFoundError: No module named 'redis'`.

## Spec tests
```text
uv run scripts/check_spec_tests.py
```
Result: no spec files missing test references.

## Behavior tests
```text
uv run pytest tests/behavior -q
```
Result: run interrupted; suite did not complete in this environment.

# Add behavior-driven test coverage

## Context
User workflows, reasoning modes, and error recovery paths lack behavior-driven
scenarios. Without BDD tests, critical flows remain unverified and extras such
as `[ui]`, `[vss]`, and `[distributed]` cannot gate execution reliably.

## Dependencies
- [configure-redis-service-for-tests](configure-redis-service-for-tests.md)

## Acceptance Criteria
- Feature files in `tests/behavior` cover `user_workflows`, `reasoning_modes`,
  and `error_recovery` markers.
- Step definitions implement each scenario and use existing `requires_*`
  markers for optional extras.
- `pytest.ini` registers any new markers.
- `uv run pytest tests/behavior -q` exercises at least one scenario for each
  marker.
- `tests/AGENTS.md` documents available markers.

## Status
Open

# Speed up task check and reduce dependency footprint

## Context
`task check` installs heavy ML packages via `uv sync --extra dev --extra test` and
runs the entire unit suite, which leads to long startup times and timeouts in
constrained environments. Recent runs hang during `pytest tests/unit -q`,
requiring manual interruption.

## Dependencies
- [improve-test-coverage-and-streamline-dependencies](
  archive/improve-test-coverage-and-streamline-dependencies.md)

## Acceptance Criteria
- Minimal install path avoids GPU and ML dependencies for `task check`.
- Unit subset exercised by `task check` completes within a few minutes on a
  fresh clone.
- Documentation clarifies extras needed for the full suite versus fast checks.
- CI workflow exercises the full suite only via manual trigger.

## Status
Open

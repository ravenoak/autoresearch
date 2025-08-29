# Speed up task check and reduce dependency footprint

## Context
`task check` previously installed heavy ML packages via `uv sync --extra dev --extra test`
and ran the entire unit suite, which led to long startup times and timeouts in
constrained environments. It now syncs only the `dev-minimal` extra and runs
`pytest` against `tests/unit/test_version.py` and `tests/unit/test_cli_help.py`
for quick smoke validation.

## Dependencies
- [improve-test-coverage-and-streamline-dependencies](
  archive/improve-test-coverage-and-streamline-dependencies.md)

## Acceptance Criteria
- Minimal install path avoids GPU and ML dependencies for `task check` by
  syncing only the `dev-minimal` extra.
- Unit subset exercised by `task check` (version and CLI smoke tests) completes
  within a few minutes on a fresh clone.
- Documentation clarifies extras needed for the full suite versus fast checks.
- CI workflow exercises the full suite only via manual trigger.

## Status
Archived

# Status

As of **August 29, 2025**, activating `.venv/bin/activate` exposes the `task` CLI.
`task check` and `task verify` pass on a clean environment with dependencies
retained. Integration and behavior suites remain skipped pending broader
coverage work, and coverage reports **100%** for exercised modules. See
[speed-up-task-check] for dependency footprint concerns and
[add-behavior-driven-test-coverage](issues/add-behavior-driven-test-coverage.md)
for behavior tests.

## Lint, type checks, and spec tests
`task check` runs linting, mypy, and a fast subset of unit tests (8 passed).

## Targeted tests
`task verify` runs 21 targeted tests with 3 skips.

## Integration tests
Not run.

## Behavior tests
Not run.

## Coverage
Total coverage is **100%**, limited to two targeted modules.
[speed-up-task-check]: issues/speed-up-task-check-and-reduce-dependency-footprint.md

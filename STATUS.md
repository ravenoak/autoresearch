# Status

As of **August 28, 2025**, activating `.venv/bin/activate` exposes the `task` CLI.
`task check` and `task verify` complete, but `uv sync --extra dev-minimal` still
prunes optional packages so only targeted unit tests run. Integration and behavior
suites remain skipped, and coverage reports **100%** for exercised modules. See
[fix-task-check-deps] for tracking.

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
[fix-task-check-deps]: issues/fix-task-check-dependency-removal-and-extension-bootstrap.md

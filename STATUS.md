# Status

As of **August 28, 2025**, activating `.venv/bin/activate` exposes the `task` CLI and
both `task check` and `task verify` complete. `uv sync --extra dev-minimal` still
prunes optional packages, so only targeted unit tests run. Coverage reports
**100%** for exercised modules. Integration and behavior suites remain skipped.
See [fix-task-check-deps] for tracking.

## Lint, type checks, and spec tests
`task check` runs linting, mypy, and spec tests successfully.

## Targeted tests
`task verify` runs 21 targeted tests with 3 skips.

## Integration tests
Not run.

## Behavior tests
Not run.

## Coverage
Total coverage is **100%**, limited to targeted modules.
[fix-task-check-deps]: issues/fix-task-check-dependency-removal-and-extension-bootstrap.md

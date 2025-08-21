# Stabilize integration test suite

## Context
Recent runs of
`uv run pytest tests/integration -m "not slow and not requires_ui and not requires_vss" -q`
show numerous failing tests and inconsistent process teardown, preventing a
reliable `task check` or `task verify` run. This blocks the 0.1.0-alpha.1
release and obscures regression detection.

## Acceptance Criteria
- Identify and resolve the failing integration tests so that the above command
  completes with zero failures.
- Ensure the test run terminates cleanly without hanging or leaving stray
  processes.
- Update documentation to outline any required services or data for integration
  tests.

## Status
Open

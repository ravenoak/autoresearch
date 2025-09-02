# Fix task verify coverage hang

## Context
Recent attempts to run `task verify` stall during the coverage phase after
syncing all extras. Earlier runs halted around 26% of the unit suite with a
`KeyError` from the `tmp_path` fixture. On September 2, 2025, the command
still required manual interruption and exited with status 201 after
`tests/unit/distributed/test_coordination_properties.py::test_message_processing_is_idempotent`
triggered a `hypothesis.errors.DeadlineExceeded`. This prevents the project
from assessing overall test health before the 0.1.0a1 release.

On September 2, 2025, another run of `uv run task verify` hung during the
coverage task. The process produced no further output for several minutes and
was manually interrupted, leaving coverage reports incomplete.

## Dependencies
- [fix-idempotent-message-processing-deadline](archive/fix-idempotent-message-processing-deadline.md)

## Acceptance Criteria
- Identify the cause of the coverage hang during `task verify`.
- Ensure the coverage phase completes and produces reports without manual
  intervention.
- Document any new requirements or limitations in `STATUS.md`.

## Status
Open

# Fix idempotent message processing deadline

## Context
`tests/unit/distributed/test_coordination_properties.py::test_message_processing_is_idempotent`
fails with `hypothesis.errors.DeadlineExceeded` during `task verify` and `task coverage`,
preventing coverage collection and blocking the release workflow.

## Dependencies

None.

## Acceptance Criteria
- Adjust the test or default Hypothesis settings so the scenario completes under the deadline.
- `task verify` and `task coverage` run without this failure.

## Status
Archived

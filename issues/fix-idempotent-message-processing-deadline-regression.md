# Fix idempotent message processing deadline regression

## Context
`task verify` fails because
`tests/unit/distributed/test_coordination_properties.py::test_message_processing_is_idempotent`
exceeds the 1s Hypothesis deadline, preventing coverage collection.

## Dependencies
- [fix-idempotent-message-processing-deadline](
  archive/fix-idempotent-message-processing-deadline.md)

## Acceptance Criteria
- Property test completes within Hypothesis's deadline.
- `task verify` runs to completion without distributed coordination failures.

## Status
Open

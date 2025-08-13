# Issue 28: Remediate unit tests after Orchestrator refactor

Unit tests fail following the attempted shift to an instance-based circuit
breaker manager. The refactor introduced API changes and incomplete updates that
leave tests in an inconsistent state.

## Context
- The in-progress refactor in issue #27 changed `_cb_manager` usage.
- Existing tests expect class-level state, causing failures and potential hangs.
- Fixtures and helper utilities may need redesign to use fresh Orchestrator
  instances per test.

## Acceptance Criteria
- Unit tests are updated to accommodate the instance-level `_cb_manager`.
- Any hanging or failing tests are fixed.
- `task test:unit` passes reliably.

## Status
Open

## Related
- #27

# Fix task verify coverage hang

## Context
Recent attempts to run `task verify` stall during the coverage phase after
syncing all extras. The run stops after roughly 26% of the unit suite and
raises a `KeyError` from the `tmp_path` fixture, requiring manual
interruption and leaving coverage reports incomplete. This prevents the
project from assessing overall test health before the 0.1.0a1 release.

## Dependencies
None.

## Acceptance Criteria
- Identify the cause of the coverage hang during `task verify`.
- Ensure the coverage phase completes and produces reports without manual
  intervention.
- Document any new requirements or limitations in `STATUS.md`.

## Status
Open

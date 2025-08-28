# Re-establish coverage gates

## Context
Coverage reporting currently runs without enforcing thresholds. Without a gate, regressions can merge unnoticed.

## Dependencies
- [fix-task-check-dependency-removal-and-extension-bootstrap](fix-task-check-dependency-removal-and-extension-bootstrap.md)

## Acceptance Criteria
- Local `task verify` and CI fail when line coverage drops below 90%.
- Coverage reports publish to artifacts and update `STATUS.md`.
- Documentation states the coverage threshold and how to run coverage checks.

## Status
Open

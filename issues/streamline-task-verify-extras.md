# Streamline task verify extras

## Context
`task verify` installs many optional extras, triggering large downloads and slow setup. Minimizing the default extras will make verification feasible in constrained environments.

## Dependencies
None.

## Acceptance Criteria
- Reduce the extras installed by default for `task verify`.
- Document how to enable heavy extras explicitly.
- `task verify` completes in a reasonable time on a fresh environment.

## Status
Open

# Install Task CLI system level

## Context
The evaluation environment still lacks the Task CLI; current setup scripts leave
`task` unavailable on PATH.

## Dependencies
None

## Acceptance Criteria
- `task --version` reports the installed version
- `task check` runs without missing-command errors
- `task verify` runs without missing-command errors

## Status
Archived

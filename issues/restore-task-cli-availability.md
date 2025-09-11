# Restore task cli availability

## Context
The environment again lacks the `task` command, preventing `task check`,
`task verify`, and `task coverage` from running. `scripts/codex_setup.sh`
completes, but `task` remains unavailable. This issue is reopened to restore
the CLI.

## Dependencies
None.

## Acceptance Criteria
- `task --version` reports a valid version after environment setup.
- Setup scripts ensure Go Task is installed or document manual steps.
- `task check` and `task verify` run successfully in a clean environment.

## Status
Open

# Restore task cli availability

## Context
The environment previously lacked the `task` command, preventing `task check`,
`task verify`, and `task coverage` from running. `scripts/setup.sh` and
`scripts/codex_setup.sh` reported "Go Task not found." This issue tracked
restoring the CLI.

## Dependencies
None.

## Acceptance Criteria
- `task --version` reports a valid version after environment setup.
- Setup scripts ensure Go Task is installed or document manual steps.
- `task check` and `task verify` run successfully in a clean environment.

## Status
Archived

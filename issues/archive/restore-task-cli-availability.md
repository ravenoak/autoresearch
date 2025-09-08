# Restore task cli availability

## Context
The environment lacks the `task` command, preventing `task check`, `task verify`,
and `task coverage` from running. Attempts to run `scripts/setup.sh` and
`scripts/codex_setup.sh` report "Go Task not found." This issue tracks restoring
the CLI.

## Dependencies
None.

## Acceptance Criteria
- `task --version` reports a valid version after environment setup.
- Setup scripts ensure Go Task is installed or document manual steps.
- `task check` and `task verify` run successfully in a clean environment.

## Status
Archived

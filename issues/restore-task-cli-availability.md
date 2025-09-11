# Restore task cli availability

## Context
The environment again lacks the `task` command, preventing `task check`,
`task verify`, and `task coverage` from running. Running `scripts/codex_setup.sh`
on September 11, 2025 completes in about 20 seconds but `task --version` still
reports `command not found`. This issue is reopened to restore the CLI.

## Dependencies
None.

## Acceptance Criteria
- `task --version` reports a valid version after environment setup.
- Setup scripts ensure Go Task is installed or document manual steps.
- `task check` and `task verify` run successfully in a clean environment.

## Status
Open

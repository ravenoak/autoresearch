# Restore task cli availability

## Context
The environment originally lacked the `task` command, preventing `task check`
and `task verify` from running. Setup now installs Go Task so both commands can
execute.

## Dependencies
None.

## Acceptance Criteria
- `task --version` reports a valid version after environment setup.
- Setup scripts ensure Go Task is installed or document manual steps.
- `task check` and `task verify` run successfully in a clean environment.

## Status
Archived

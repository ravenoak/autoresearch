# Restore task cli availability

## Context
The current environment lacks the `task` command, preventing `task check` and
`task verify` from running. This regression blocks linting and tests,
contradicting previous setup expectations.

## Dependencies
None.

## Acceptance Criteria
- `task --version` reports a valid version after environment setup.
- Setup scripts ensure Go Task is installed or document manual steps.
- `task check` and `task verify` run successfully in a clean environment.

## Status
Open

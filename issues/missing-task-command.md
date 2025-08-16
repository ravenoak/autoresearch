# Missing task command after setup

## Context
- `task --version` returns `command not found` in the prepared environment.
- Root guidelines expect Go Task to be available under `/usr/local/bin/task`.

## Acceptance Criteria
- `task --version` reports a valid version after environment setup.
- Setup scripts install Go Task or document manual installation steps.
- Documentation stays in sync with tooling requirements.

## Status
Open

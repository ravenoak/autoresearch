# Ensure Go Task CLI availability

## Context
The project relies on the Go Task CLI to run `task check` and `task verify`. In
clean environments the CLI is absent, leading to errors such as `error: Failed
to spawn: 'task'` and blocking test workflows. Developers must manually install
the tool, but setup guidance does not cover this requirement.

## Dependencies
None.

## Acceptance Criteria
- Provide a bootstrap script or documented steps to install the Go Task CLI.
- After installation `task check` runs successfully in a fresh environment.
- Update setup documentation to mention the bootstrap process.

## Status
Open

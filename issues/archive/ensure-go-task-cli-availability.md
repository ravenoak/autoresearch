# Ensure Go Task CLI availability

## Context
The project relies on the Go Task CLI to run `task check` and `task verify`. In
clean environments the CLI is absent, leading to errors such as `error: Failed
to spawn: 'task'` and blocking test workflows. Developers must manually install
the tool, but setup guidance does not cover this requirement.

On September 5, 2025, installing the CLI via the official script placed the
binary under `.venv/bin`, but `task check` still failed with "executable file
not found in $PATH" until the directory was exported to `PATH`.

## Dependencies
None.

## Acceptance Criteria
- Provide a bootstrap script or documented steps to install the Go Task CLI.
- After installation `task check` runs successfully in a fresh environment.
- Update setup documentation to mention the bootstrap process.

## Status
Archived

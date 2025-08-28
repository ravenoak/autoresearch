# Document task CLI requirement

## Context
Attempts to run `task install` fail when the Go Task CLI is missing. The
repository relies on the `task` binary to execute setup and test commands, but
current instructions do not ensure it is available on fresh systems. Without it
contributors cannot run `task check` or `task verify`.

## Dependencies
- None

## Acceptance Criteria
- Setup explicitly installs or verifies the Go Task CLI.
- `README.md` or `scripts/setup.sh` describes how to install `task` on supported
  platforms.
- `task --version` succeeds after following the documented steps.
- `task install` completes on a clean clone without manual intervention.

## Status
Open

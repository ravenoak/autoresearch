# Document environment bootstrap

## Context
Setting up the development environment currently requires manually installing the `task` binary and running `uv sync`. The `scripts/codex_setup.sh` script aborted during `apt-get update`, leaving `task` uninstalled. Clear instructions are needed so contributors can reproduce the expected setup.

## Acceptance Criteria
- Update README and setup docs with explicit steps to install `task` and run `task install`.
- Ensure `scripts/codex_setup.sh` handles package manager failures gracefully and installs required tools.
- Verify a fresh clone can run `task check` successfully using the documented steps.

## Status
Open

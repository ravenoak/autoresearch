# Document environment bootstrap

## Context
Environment setup instructions are now centralized in
[docs/installation.md](../../docs/installation.md). Prior to consolidation,
contributors had to manually install the `task` binary and run `uv sync`.
The previous setup script sometimes aborted during `apt-get update`.
This left `task` uninstalled. Clear guidance ensures contributors can
reproduce the expected setup.

## Acceptance Criteria
- Consolidate setup steps in
  [docs/installation.md](../../docs/installation.md), including how to install
  `task` and run `task install`.
- Ensure the setup script handles package manager failures gracefully
  and installs required tools.
- Verify a fresh clone can run `task check` successfully using the documented
  steps.

## Status
Archived

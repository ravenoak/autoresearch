# Document environment bootstrap

## Context
Environment setup instructions are now centralized in
[docs/installation.md](../../docs/installation.md). Prior to consolidation,
contributors had to manually install the `task` binary and run `uv sync`.
`scripts/codex_setup.sh` sometimes aborted during `apt-get update`, leaving
`task` uninstalled. Clear guidance ensures contributors can reproduce the
expected setup.

## Acceptance Criteria
- Consolidate setup steps in
  [docs/installation.md](../../docs/installation.md), including how to install
  `task` and run `task install`.
- Ensure `scripts/codex_setup.sh` handles package manager failures gracefully
  and installs required tools.
- Verify a fresh clone can run `task check` successfully using the documented
  steps.

## Status
Archived

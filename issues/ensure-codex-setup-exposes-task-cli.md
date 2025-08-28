# Ensure Codex setup exposes task CLI

## Context
Running `scripts/codex_setup.sh` installs Go Task but leaves `.venv/bin` outside `PATH`, causing `task` to be unavailable unless users manually modify their environment. This interrupts the initial workflow in the Codex evaluation environment.

## Dependencies
- [synchronize-codex-and-generic-setup-scripts](synchronize-codex-and-generic-setup-scripts.md)

## Acceptance Criteria
- `scripts/codex_setup.sh` makes the `task` command available immediately after execution or clearly instructs activation steps.
- `task --version` succeeds without manual `PATH` edits after running `scripts/codex_setup.sh`.
- Codex-specific documentation reflects any required activation or PATH configuration.

## Status
Open

# Ensure task CLI available after setup

## Context
The Codex evaluation environment's setup installs Go Task but leaves `.venv/bin` outside
`PATH`, causing `task` to be unavailable unless users manually modify their environment.
This interrupts the initial workflow in the evaluation environment.

## Dependencies
- [synchronize-codex-and-generic-setup-scripts](synchronize-codex-and-generic-setup-scripts.md)

## Acceptance Criteria
- The setup process makes the `task` command available immediately after execution or
  clearly instructs activation steps.
- `task --version` succeeds without manual `PATH` edits after running the setup.
- Codex-specific documentation reflects any required activation or PATH configuration.

## Status
Open

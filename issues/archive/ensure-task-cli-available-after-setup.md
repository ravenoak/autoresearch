# Ensure task CLI available after setup

## Context
Previously the Codex environment's setup installed Go Task but left
`.venv/bin` outside `PATH`, leaving `task` unavailable. The setup scripts now
append `.venv/bin` to `PATH` or instruct activation and validate the CLI with
`task --version`.

## Dependencies
- [synchronize-codex-and-generic-setup-scripts](../synchronize-codex-and-generic-setup-scripts.md)

## Acceptance Criteria
- The setup process makes the `task` command available immediately after
  execution or clearly instructs activation steps.
- `task --version` succeeds without manual `PATH` edits after running the
  setup.
- Codex-specific documentation reflects any required activation or PATH
  configuration.

## Status
Archived

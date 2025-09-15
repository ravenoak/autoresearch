# Expose task CLI after codex setup

## Context
Running `scripts/codex_setup.sh` prints that `.venv/bin` was appended to `PATH`,
but the parent shell does not retain the change. `task` remains unavailable
unless commands are invoked as `uv run task` or the virtual environment is
activated manually. Attempting to install the CLI with `apt-get install -y task`
fails with "Unable to locate package task".

## Dependencies
None.

## Acceptance Criteria
- Running `scripts/codex_setup.sh` exposes `task` in the current shell or
  documents activation steps.
- `task --version` succeeds immediately after the script completes.
- STATUS.md notes the updated setup instructions.

## Status
Archived

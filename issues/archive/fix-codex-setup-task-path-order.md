# Fix Codex setup task path order

## Context
Codex environment bootstrap installed Go Task but ran `scripts/setup.sh` before
`.venv/bin` was added to `PATH`, causing setup to abort with "Go Task not found".
The script now appends the virtual environment's `bin` directory to `PATH`
immediately after installation so `task` is discoverable.

## Dependencies
- None

## Acceptance Criteria
- `scripts/codex_setup.sh` completes without Go Task errors.
- `task` command is available during setup.
- `.venv/bin` remains on `PATH` after the script finishes.

## Status
Archived

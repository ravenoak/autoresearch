# Document test dependency setup

## Context
Running `uv run pytest` fails with `ModuleNotFoundError: No module named 'pytest_bdd'` because
the development `[test]` extra is not installed when the `task` CLI is unavailable. Contributors
lack guidance for installing these dependencies manually.

## Dependencies
- [restore-task-cli-availability](archive/restore-task-cli-availability.md)

## Acceptance Criteria
- Document manual installation steps for `[test]` extras in `README.md` or `STATUS.md`.
- Ensure `scripts/setup.sh` installs `[test]` dependencies when the `task` CLI is missing.
- After setup, `uv run pytest tests/unit -q` executes without missing plugin errors.

## Status
Open

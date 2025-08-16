# Codex setup missing Go Task and dev dependencies

## Context
- Starting environment lacked `task` command and dev packages like `pytest`.
- Root guidelines expect `scripts/codex_setup.sh` to install Go Task system-wide and dev dependencies.
- Manual install of Go Task and running `uv pip install -e '.[full,dev]'` were required.
- Verify whether `codex_setup.sh` failed or needs adjustments to ensure tools are available.

## Acceptance Criteria
- Go Task (`task`) is available after running setup.
- Dev dependencies including `pytest` are installed in `.venv`.
- Update `scripts/codex_setup.sh` and documentation if additional steps are required.

## Status
Open

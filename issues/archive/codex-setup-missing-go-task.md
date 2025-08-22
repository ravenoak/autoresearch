# Codex setup missing Go Task and dev dependencies

## Context
- Starting environment lacked `task` command and dev packages like `pytest`.
- Root guidelines expect the setup script to install Go Task system-wide and
  dev dependencies.
- After installing Go Task and running `uv pip install -e '.[dev]'`,
  `which pytest` resolves to `.venv/bin/pytest` and
  `uv run pytest -q` executes without missing-module errors.

## Acceptance Criteria
- Go Task (`task`) is available after running setup.
- Dev dependencies including `pytest`, `flake8`, and `typer` are installed in `.venv`.
- `which pytest` resolves to `.venv/bin/pytest`.
- `uv run pytest -q` completes without missing-module errors.
- Update setup scripts and documentation if additional steps are required.

## Status
Archived

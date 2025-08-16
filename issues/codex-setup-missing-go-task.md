# Codex setup missing Go Task and dev dependencies

## Context
- Starting environment lacked `task` command and dev packages like `pytest`.
- Root guidelines expect `scripts/codex_setup.sh` to install Go Task system-wide and dev dependencies.
- Manual install of Go Task and running `uv pip install -e '.[full,dev]'` were required.
- Verify whether `codex_setup.sh` failed or needs adjustments to ensure tools are available.
- `which pytest` resolves to a Pyenv shim instead of `.venv/bin/pytest`.
- `uv pip list | grep flake8` shows that linting tools are not present.
- `uv run pytest -q` fails with `ModuleNotFoundError: No module named 'typer'`.

## Acceptance Criteria
- Go Task (`task`) is available after running setup.
- Dev dependencies including `pytest`, `flake8`, and `typer` are installed in `.venv`.
- `which pytest` resolves to `.venv/bin/pytest`.
- `uv run pytest -q` completes without missing-module errors.
- Update `scripts/codex_setup.sh` and documentation if additional steps are required.

## Status
Open

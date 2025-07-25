# Developer Guide

This guide describes how to set up a development environment and the expected workflow for contributing changes.

The project now uses **uv** for dependency management instead of Poetry. All
commands below rely on `uv`.

## Environment Setup

1. Create a virtual environment:
   ```bash
   uv venv
   ```
2. Install dependencies including development tools and all optional extras:
   ```bash
   uv sync --all-extras
   uv pip install -e .
   ```
   Run `uv lock` whenever `pyproject.toml` changes so the lock file stays current.
3. Activate the environment with `source .venv/bin/activate` before running commands.

Several unit and integration tests require `gitpython` and the DuckDB VSS
extension. Both are installed when you set up the environment with
`uv pip install --all-extras`.

## Code Style

- Run code format and style checks before committing:
 ```bash
  uv run flake8 src tests
  uv run mypy src
  ```
- Public modules and functions should include concise docstrings.
- Keep commits focused and avoid temporary files.

## Pull Request Process

1. Create a feature branch and commit your changes.
2. Run the full test suite:
   ```bash
   uv run pytest -q
   uv run pytest tests/behavior
   ```
   Ensure the `.venv` is active before running these commands.

### Running only fast tests

For quick feedback, you can skip heavy integration tests marked with
`@pytest.mark.slow`:

```bash
uv run pytest -m "not slow" -q
uv run pytest -m "not slow" tests/behavior
```
To run the heavier tests separately:

```bash
uv run pytest -m slow
```
Distributed execution scenarios and other long-running integrations are
decorated with `@pytest.mark.slow`.
3. Update or add documentation when needed.
4. Open a pull request explaining the rationale for the change.

See `CONTRIBUTING.md` for additional information on contributing.

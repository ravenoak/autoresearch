# Developer Guide

This guide describes how to set up a development environment and the expected workflow for contributing changes.

The project uses **uv** for dependency management. All commands below rely on
`uv`.

## Environment Setup

1. Create a virtual environment:
   ```bash
   uv venv
   ```
2. Install dependencies including development tools and all optional extras:
   ```bash
   uv pip install -e '.[full,parsers,git,llm,dev]'
   ```
   Run `uv lock` whenever `pyproject.toml` changes so the lock file stays current.
3. Activate the environment with `source .venv/bin/activate` before running commands.

Several unit and integration tests require `gitpython` and the DuckDB VSS
extension. Include the `git` extra when setting up the environment, for example:
`uv pip install -e '.[full,parsers,git,llm,dev]'`.

## Code Style

- Run code format and style checks before committing:
 ```bash
  uv run flake8 src tests
  uv run mypy src
  ```
- Public modules and functions should include concise docstrings.
- Keep commits focused and avoid temporary files.

## Lifecycle Management

Some components maintain global state such as configuration watchers and HTTP
sessions. Tests must clean up these resources to avoid interference:

- Use ``with ConfigLoader() as loader`` or call ``ConfigLoader.reset_instance()``
  to stop watcher threads and clear cached configuration.
- Call ``Search.reset()`` to restore backend registries, release any loaded
  sentence transformer model and close pooled HTTP sessions.

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

### Combined test execution and coverage

Run unit, integration and behavior tests in the same session to ensure a consistent environment. Collect coverage from each suite and combine the results:

```bash
coverage run -p -m pytest -q
coverage run -p -m pytest tests/integration -q
coverage run -p -m pytest tests/behavior -q
coverage combine
```

Use the markers `requires_ui`, `requires_vss` and `slow` to skip heavy tests during development.
`requires_ui` indicates tests that rely on the `ui` extra while `requires_vss`
marks tests that depend on the `vss` extra. Skip them with:

```bash
uv run pytest -m "not requires_ui and not requires_vss and not slow"
```
3. Update or add documentation when needed.
4. Open a pull request explaining the rationale for the change.

See `CONTRIBUTING.md` for additional information on contributing.

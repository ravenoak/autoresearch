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

### Virtual environment best practices

- Keep the `.venv` isolated by avoiding global package installs.
- Always activate the environment or prefix commands with `uv run`.
- Regenerate the lock file with `uv lock` when dependencies change and
  reinstall using `uv pip install -e '.[full,parsers,git,llm,dev]'`.
- Use `task verify` to run linting and tests inside the active environment.

## Code Style

- Run code format and style checks before committing:
 ```bash
  uv run flake8 src tests
  uv run mypy src
  ```
- Public modules and functions should include concise docstrings.
- Keep commits focused and avoid temporary files.

## Typing and third-party stubs

- Place third-party stubs under ``tests/stubs`` so ``MYPYPATH`` picks them up
  during ``mypy`` runs. Reuse the existing package layout. For example,
  ``tests/stubs/fastembed`` mirrors the runtime module structure with ``.pyi``
  files or ``__init__.py`` shims.
- Co-locate stubs inside ``src/`` only when they describe our own packages or
  when a ``.pyi`` beside a module lets mypy see attributes that are generated at
  runtime. Keep project-owned stubs in the same directory tree as the Python
  module they document.
- Gate optional imports behind ``if TYPE_CHECKING`` so heavy dependencies stay
  optional at runtime while types remain available to the checker. Recent
  examples include ``src/autoresearch/search/context.py`` (guards ``spacy`` and
  ``BERTopic``) and ``src/autoresearch/orchestration/state.py`` (exposes the
  ``QueryStateLike`` protocol without importing it eagerly).
- When adding new shims, extend the PR 1 stubs for ``pydantic``, ``fastapi``,
  ``starlette``, ``requests``, ``psutil``, ``pynvml``, ``spacy``,
  ``sentence_transformers``, ``bertopic``, ``fastembed``, ``pdfminer.layout``,
  and ``owlrl``. These live under ``tests/stubs`` and establish the expected
  method and attribute surface for strict type checking. Reuse their patterns
  when introducing additional modules or expanding coverage.

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

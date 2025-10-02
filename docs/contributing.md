# Contributing

We welcome contributions via pull requests. Autoresearch uses **uv** for environment management.
Install the development dependencies first:

```bash
uv venv
uv pip install -e '.[full,parsers,git,llm,dev]'
```
Run `uv lock` after modifying dependencies to update `uv.lock` before syncing.

You can alternatively run the helper script. It refreshes the lock file when
needed, installs all extras with `uv pip install -e '.[full,parsers,git,llm,dev]'` and links the
package in editable mode:

```bash
./scripts/setup.sh
```

## Running tests

Execute the commands below before opening a pull request:

```bash
uv run flake8 src tests
uv run mypy src
uv run mypy --strict tests/behavior
uv run pytest -q
uv run pytest tests/behavior
```

Maintain at least 90% test coverage and remove temporary files before submitting your changes. After running tests, clean up any untracked artifacts such as `kg.duckdb`, `rdf_store`, and `__pycache__` so your working directory stays tidy.

Please keep commits focused and descriptive.


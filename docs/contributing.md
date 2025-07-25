# Contributing

We welcome contributions via pull requests. Install the development dependencies first:

```bash
uv venv
uv pip install --all-extras
uv pip install -e .
```

You can alternatively run the helper script. It refreshes the lock file when
needed, installs all extras with `uv pip install --all-extras` and links the
package in editable mode:

```bash
./scripts/setup.sh
```

## Running tests

Execute the commands below before opening a pull request:

```bash
flake8 src tests
mypy src
pytest -q
pytest tests/behavior
```

Maintain at least 90% test coverage and remove temporary files before submitting your changes.

Please keep commits focused and descriptive.


# Contributing

We welcome contributions via pull requests. Install the development dependencies first:

```bash
poetry install --with dev
```

You can alternatively run the helper script to install all dependencies:

```bash
./scripts/setup.sh
```

## Running tests

Execute the commands below before opening a pull request:

```bash
poetry run flake8 src tests
poetry run mypy src
poetry run pytest -q
poetry run pytest tests/behavior
```

Maintain at least 90% test coverage and remove temporary files before submitting your changes.

Please keep commits focused and descriptive.

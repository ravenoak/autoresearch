# Contributing

We welcome contributions via pull requests. To get started, install the development dependencies and run the tests:

```bash
poetry install --with dev
poetry run flake8 src tests
poetry run mypy src
poetry run pytest
poetry run pytest tests/behavior
```

Please keep commits focused and descriptive.

# Developer Guide

This guide describes how to set up a development environment and the expected workflow for contributing changes.

## Environment Setup

1. Install [Poetry](https://python-poetry.org/docs/#installation).
2. Select the Python interpreter:
   ```bash
   poetry env use $(which python3)
   ```
3. Install dependencies including development tools and all optional extras:
   ```bash
   poetry install --with dev --all-extras
   ```
4. Activate the environment with `poetry shell` or prefix commands with `poetry run`.

Several unit and integration tests require `gitpython` and the DuckDB VSS
extension. Both are installed when you set up the environment with
`poetry install --with dev --all-extras`.

## Code Style

- Run code format and style checks before committing:
 ```bash
  poetry run flake8 src tests
  poetry run mypy src
  ```
- Public modules and functions should include concise docstrings.
- Keep commits focused and avoid temporary files.

## Pull Request Process

1. Create a feature branch and commit your changes.
2. Run the full test suite:
   ```bash
   poetry run pytest -q
    poetry run pytest tests/behavior
    ```
    All testing commands should be executed with `poetry run` to use the
    project's virtual environment.

### Running only fast tests

For quick feedback, you can skip heavy integration tests marked with
`@pytest.mark.slow`:

```bash
poetry run pytest -m "not slow" -q
poetry run pytest -m "not slow" tests/behavior
```
To run the heavier tests separately:

```bash
poetry run pytest -m slow
```
3. Update or add documentation when needed.
4. Open a pull request explaining the rationale for the change.

See `CONTRIBUTING.md` for additional information on contributing.

# Contribution Guidelines

- Install dependencies with `poetry install` or `pip install -e .` before running tests.
- Check style with `poetry run flake8 src tests` and type hints with `poetry run mypy src`.
- Run `pytest -q` and the BDD tests in `tests/behavior` before opening a pull request.
- Keep commits focused and provide clear messages describing your changes.
- Remove temporary files and keep the repository tidy.

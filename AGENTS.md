# Contribution Guidelines

Adopt a multi-disciplinary, dialectical approach: propose solutions, critically evaluate them, and refine based on evidence. Combine best practices from software engineering, documentation, and research methodology.

## Environment setup
- Use **Poetry** for all project interactions.
  - Select the Python interpreter with `poetry env use $(which python3)` (Python 3.12 or newer).
  - Install dependencies with `poetry install --with dev`.
  - Activate the environment using `poetry shell` or prefix commands with `poetry run`.
  - Avoid system-level Python or `pip`. Run `pip install -e .` only inside the Poetry virtual environment using `poetry shell` or `poetry run pip`.

## Verification steps
- Check code style with `poetry run flake8 src tests`.
- Verify type hints with `poetry run mypy src`.
- Run the unit suite: `poetry run pytest -q`.
- Execute BDD tests in `tests/behavior`: `poetry run pytest tests/behavior`.

## Commit etiquette
- Keep commits focused and write clear messages detailing your reasoning.
- Remove temporary files and keep the repository tidy.

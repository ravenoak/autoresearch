# Contribution Guidelines

> Special note: the environment that ChatGPT Codex operates in executes `scripts/codex_setup.sh` for setup. If it fails, a `CODEX_ENVIRONMENT_SETUP_FAILED` file will be created.

Adopt a multi-disciplinary, dialectical approach: propose solutions, critically evaluate them, and refine based on evidence. Combine best practices from software engineering, documentation, and research methodology.

## Environment setup
- Use **Poetry** for all project interactions.
  - Select the Python interpreter with `poetry env use $(which python3)` (Python 3.12 or newer).
  - Install dependencies with `poetry install --with dev --all-extras` to ensure optional
    packages used by the tests are available.
  - Activate the environment using `poetry shell` or prefix commands with `poetry run`.
  - Avoid system-level Python or `pip`. Run `pip install -e .` only inside the Poetry virtual environment using `poetry shell` or `poetry run pip`.
  - Codex environments run `scripts/codex_setup.sh`, which delegates to `scripts/setup.sh` and installs all dev dependencies so tools like `flake8`, `mypy`, and `pytest` are available.

## Verification steps
- Check code style with `poetry run flake8 src tests`.
- Verify type hints with `poetry run mypy src`.
- Run the unit suite: `poetry run pytest -q`.
- Execute BDD tests in `tests/behavior`: `poetry run pytest tests/behavior`.

## Commit etiquette
- Keep commits focused and write clear messages detailing your reasoning.
- Remove temporary files and keep the repository tidy.

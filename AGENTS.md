# Contribution Guidelines

> Special note: the environment that ChatGPT Codex operates in executes `scripts/codex_setup.sh` for setup. If it fails, a `CODEX_ENVIRONMENT_SETUP_FAILED` file will be created.

Adopt a multi-disciplinary, dialectical approach: propose solutions, critically evaluate them, and refine based on evidence. Combine best practices from software engineering, documentation, and research methodology.

## Environment setup
- Use **uv** for dependency management and project interactions.
  - Create a virtual environment with `uv venv`.
  - Install dependencies with `uv pip install -e '.[full,dev]'`.
  - Activate the environment using `source .venv/bin/activate` or prefix commands with `uv pip`.
  - When modifying `pyproject.toml`, regenerate the lock file with `uv lock` before reinstalling.
  - Codex environments run `scripts/codex_setup.sh`, which delegates to `scripts/setup.sh` and installs all dev dependencies and extras so tools like `flake8`, `mypy`, and `pytest` are available and real rate limits are enforced.
  - Confirm dev tools are installed with `uv pip list | grep flake8`.

## Verification steps
- Check code style with `uv run flake8 src tests`.
- Verify type hints with `uv run mypy src`.
- Run the unit suite: `uv run pytest -q`.
- Execute BDD tests in `tests/behavior`: `uv run pytest tests/behavior`.
- Run the entire suite with coverage using `task coverage`.

## Commit etiquette
- Keep commits focused and write clear messages detailing your reasoning.
- Remove temporary files and keep the repository tidy.

## Legacy workflow
Autoresearch previously relied on **Poetry**. Use `uv venv` to create the
environment, `uv pip install -e '.[full,dev]'` to install dependencies, and `uv run <cmd>`
to invoke tools. Run `uv run pip install -e .` if you need an editable install.

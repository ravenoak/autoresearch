# Contribution Guidelines

> Special note: the environment that ChatGPT Codex operates in executes `scripts/codex_setup.sh` for setup. If it fails, a `CODEX_ENVIRONMENT_SETUP_FAILED` file will be created.

Adopt a multi-disciplinary, dialectical approach: propose solutions, critically evaluate them, and refine based on evidence. Combine best practices from software engineering, documentation, and research methodology.

## Environment setup
- Use **uv** for dependency management and project interactions.
  - Python **3.12 or newer** is required. Confirm with `python --version`.
  - Create a virtual environment with `uv venv`.
    - `scripts/setup.sh` verifies the interpreter and fails if it is too old.
  - Install dependencies with `uv pip install -e '.[full,dev]'`.
  - Activate the environment using `source .venv/bin/activate` or prefix commands with `uv pip`.
  - When modifying `pyproject.toml`, regenerate the lock file with `uv lock` before reinstalling.
  - Codex environments run `scripts/codex_setup.sh`, which delegates to `scripts/setup.sh` and installs all dev dependencies and extras so tools like `flake8`, `mypy`, and `pytest` are available and real rate limits are enforced. The setup script also installs [Go Task](https://taskfile.dev) system-wide so `task` commands work out of the box. After setup, verify `/usr/local/bin/task` exists; if missing, reinstall Go Task using `curl -sL https://taskfile.dev/install.sh | sh -s -- -b /usr/local/bin`.
  - Confirm dev tools are installed with `uv pip list | grep flake8`.
  - After running `scripts/codex_setup.sh`, verify `pytest-cov`, `tomli_w`, and `hypothesis` are present using `uv pip list`.

## Verification steps
- Check code style with `uv run flake8 src tests`.
- Verify type hints with `uv run mypy src`.
- Run the unit suite: `uv run pytest -q`.
- Execute BDD tests in `tests/behavior`: `uv run pytest tests/behavior`.
- Run the entire suite with coverage using `task coverage`. If `task` is unavailable, run `uv run pytest --cov=src` instead.

## Commit etiquette
- Keep commits focused and write clear messages detailing your reasoning.
- Remove temporary files and keep the repository tidy.

## Legacy workflow
Autoresearch previously relied on **Poetry**. Use `uv venv` to create the
environment, `uv pip install -e '.[full,dev]'` to install dependencies, and `uv run <cmd>`
to invoke tools. Run `uv run pip install -e .` if you need an editable install.

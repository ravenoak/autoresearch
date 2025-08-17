# Contribution Guidelines

> Special note: before work begins, `scripts/codex_setup.sh` is executed to set up the environment. If it fails, a `CODEX_ENVIRONMENT_SETUP_FAILED` file will be created. If this marker is present, inspect `codex_setup.log` for details. This guide is the only document that may mention `scripts/codex_setup.sh`; do not reference it elsewhere.

Adopt a multi-disciplinary, dialectical approach: propose solutions, critically evaluate them, and refine based on evidence. Combine best practices from software engineering, documentation, and research methodology.

## AGENTS files and scope rules
- Place `AGENTS.md` in any directory that needs custom instructions.
- Instructions apply to the file's directory and all of its descendants.
- Deeper `AGENTS.md` files override conflicting instructions from parent directories.
- Keep `AGENTS.md` files current and commit updates alongside related code changes.
- When instructions affect environment setup or tooling, update `scripts/codex_setup.sh` to match.
- Changes to tooling must be reflected in both this document and `scripts/codex_setup.sh` so documentation and setup stay in sync.
- Changes under `tests/` must keep this document and `scripts/codex_setup.sh` in sync to reflect new test requirements.

## Date references
- Use the container's system clock for current dates.
- Derive past dates from `git log` commit timestamps.
- Format dates consistently (e.g., `August 17, 2025`).

## Issue tracking
- Track work items in the `/issues` directory.
- If the issue tracker directory moves or is renamed, update this section to reference the new location.
- Tickets follow the template and style guide in [`issues/README.md`](issues/README.md).
- File names must be slugged titles; numeric identifiers in filenames or content are prohibited. Reference issues by slugged filename.
- In `CHANGELOG.md`, link issues using their slugged filenames (for example, `issues/archive/example-issue.md`) and avoid numeric prefixes.
- When work is finished, set `Status` to `Archived` and move the ticket to `/issues/archive/` without renaming.
- When issue tooling changes, update this file, `issues/AGENTS.md`, and `scripts/codex_setup.sh` to keep documentation and setup aligned.

## Binary artifacts
- Do not commit binary files such as `.duckdb_extension` modules.
- Required binaries are downloaded during setup and referenced via `VECTOR_EXTENSION_PATH`.
- The `extensions` directory is tracked only with a placeholder to keep it empty.

## Environment setup
- `scripts/codex_setup.sh` sets up your environment prior to being handed off to you; update it whenever AGENTS guidelines or environment requirements change so the automated setup stays in sync.
- Update this file, your instructions and initial context, as appropriate and according to best-practices.
- Documents in `docs/inspirational_docs/` are for inspiration only and must not be directly referenced; use these documents for inspiration.
- Documents in `docs/external_research_papers/` are copies of academic papers and can be referenced using best-practices.
- Use **uv** for dependency management and project interactions.
  - **Run all commands inside the `uv` virtual environment.** Activate it with `source .venv/bin/activate` or prefix commands with `uv run` or `uv pip`.
  - Python **3.12 or newer** is required. Confirm with `python3 --version`.
  - Create a virtual environment with `uv venv`.
    - Quick start: `uv venv && uv sync --all-extras`.
    - `scripts/setup.sh` verifies the interpreter and fails if it is too old.
    - Both setup scripts abort if `python3` is missing or older than 3.12.
    - Install dependencies and extras:
      - Run `uv sync --all-extras` followed by `uv pip install -e .` for the standard setup.
      - Use `uv pip install -e '.[full,dev]'` only to reinstall dependencies if tools are missing or `uv sync` is unavailable.
  - When modifying `pyproject.toml`, regenerate `uv.lock` with `uv lock` before reinstalling.
    `uv.lock` is the authoritative lock file; do not commit `poetry.lock`.
    - Codex environments run `scripts/codex_setup.sh`, which delegates to `scripts/setup.sh` and installs all dev dependencies and extras with `uv sync --all-extras` so tools like `flake8`, `mypy`, and `pytest` are available and real rate limits are enforced. The setup script installs [Go Task](https://taskfile.dev) inside the virtual environment. After setup, ensure `task`, `flake8`, and `pytest` resolve to paths under `.venv/bin`.
    - Confirm dev tools are installed with `uv pip list | grep flake8`.
    - Verify each CLI tool runs from the virtual environment:
      - `task --version`
      - `flake8 --version`
      - `pytest --version`
      - `mypy --version`
      If any command is missing, rerun `scripts/codex_setup.sh` or reinstall
      with `uv sync --all-extras && uv pip install -e .`.
  - After running `scripts/codex_setup.sh`, verify `pytest`, `pytest-bdd`, `pytest-httpx`, `pytest-cov`, `flake8`, `hypothesis`, `tomli_w`, `freezegun`, `duckdb-extension-vss`, `a2a-sdk`, `GitPython`, `pdfminer-six`, `python-docx`, `sentence-transformers`, `transformers`, `spacy`, `bertopic`, `fastapi`, `responses`, `uvicorn`, and `psutil` are present using `uv pip list`.
- `VECTOR_EXTENSION_PATH` selects the DuckDB vector search extension. Tests
    must either disable the `vector_extension` entirely or point this variable
    to the stub at `extensions/vss_stub.duckdb_extension`. Set it to a real
    `vss.duckdb_extension` only when the actual extension is available.
  - If `CODEX_ENVIRONMENT_SETUP_FAILED` exists, inspect
    `codex_setup.log` for setup details.

### Offline setup
- Use local Python packages when network access is unavailable.
  - Place pre-downloaded wheels under `./wheels` and source archives under
    `./archives`.
  - Before running `scripts/codex_setup.sh`, export `WHEELS_DIR` and
    `ARCHIVES_DIR` to point at these directories. The setup script installs
    them with `uv pip --no-index`.
- Pre-download DuckDB extensions with `scripts/download_duckdb_extensions.py`
  and set `VECTOR_EXTENSION_PATH` to the local `.duckdb_extension` file. If a
  real extension is not available, leave `VECTOR_EXTENSION_PATH` unset and the
  setup script will default to `extensions/vss_stub.duckdb_extension`.
- Keep this section and `scripts/codex_setup.sh` in sync when offline
  requirements change.

## Verification steps
- Always run tests with `uv run` or inside the activated `.venv`; all tests
  must run inside this environment.
- Verify the environment by running `which pytest` and ensure it resolves
  to `.venv/bin/pytest`.
- Confirm tool availability and versions:
  - `task --version`
  - `flake8 --version`
  - `mypy --version`
  - `pytest --version`
  If any command fails, reinstall with `uv sync --all-extras` or rerun
  `scripts/codex_setup.sh`.
- Run `task verify` before committing; it performs linting, type checking,
  and all tests with coverage (see [`Taskfile.yml`](Taskfile.yml)).
- Generate explicit coverage reports with `task coverage`.
- Use `rg` for repository searches instead of `grep -R` or `ls -R`.
  Example: `rg <pattern>`.
- If `task` is unavailable, run these commands individually:
  - Format code with `uv run black .`.
  - Sort imports with `uv run isort .`.
  - Format with `uv run ruff format src tests`.
  - Lint with `uv run ruff check --fix src tests`.
  - Check code style with `uv run flake8 src tests`.
  - Verify type hints with `uv run mypy src`.
  - Run the unit suite: `uv run pytest -q`.
  - Execute BDD tests in `tests/behavior`: `uv run pytest tests/behavior`.
  - Run the entire suite with coverage: `uv run pytest --cov=src`.
  - Execute any targeted tests in `tests/targeted` separately and fold them into the
    main test directories once validated.
- Requests to the `/metrics` endpoint must include an API key mapped to a role
  with the `metrics` permission (the default `admin` role works). Tests hitting
  this endpoint should set the `X-API-Key` header accordingly.
- Before running any tests, install the development extras with
  `uv pip install -e '.[full,parsers,git,llm,dev]'`. These extras are required
  for full test runs, including integration and behavior tests.
- Install optional NLP extras with `uv pip install -e '.[nlp]'` when running
  tests that depend on topic modeling or transformer features. These tests use
  the `requires_nlp` marker and are typically marked `slow`; run them with
  `task test:slow` or `uv run pytest -m requires_nlp`. Skip them with
  `-m 'not requires_nlp'` if the extras are unavailable.
  - See [tests/behavior/README.md](tests/behavior/README.md) for markers
    such as `requires_ui`, `requires_vss`, `requires_git`, and `requires_nlp` to select specific scenarios.
  - Tag tests that rely on optional extras with the appropriate marker
    (`requires_ui`, `requires_vss`, `requires_git`, or `requires_nlp`). When
    introducing new markers, update this document and `scripts/codex_setup.sh`
    so setup remains in sync.

### Cleanup
- Run `task clean` to remove `__pycache__` and `.mypy_cache` directories.
- Manually remove test artifacts such as `kg.duckdb` and `rdf_store` if present.

## Utility scripts and Taskfile commands
- Run `task --list` to discover helper commands.
- Run `uv run scripts/smoke_test.py` to perform a quick environment smoke test.
- After deploying the service, verify configuration and health with `uv run scripts/deploy.py`.
- Check token usage against baselines with `uv run scripts/check_token_regression.py` or `task check-baselines`.
- Publish a development build to TestPyPI with `uv run scripts/publish_dev.py`.
- Additional utilities in `scripts/` include:
  - `benchmark_token_memory.py` for performance baselines
  - `evaluate_ranking.py`, `optimize_search_weights.py`, `visualize_rdf.py`, and `upgrade.py`
- [`Taskfile.yml`](Taskfile.yml) provides additional helpers:
  - `task unit`, `task integration`, and `task behavior` run their respective test suites.
  - `task test:all` executes the entire suite, and `task coverage` produces coverage reports.
  - `task check-baselines` enforces token regression thresholds.
  - `task wheels` builds wheels for all platforms.
- When new scripts or tasks are added, update both this file and `scripts/codex_setup.sh` accordingly.

## GitHub Actions workflows
- The CI workflow in `.github/workflows/ci.yml` is dispatch-only.
- All workflows must be dispatch-only or remain disabled in `.github/workflows.disabled`.
- Disabled workflow files must start with `# NOTE: This workflow is disabled. Move to .github/workflows to enable.`
- Standardize on these actions versions:
  - `actions/checkout@v4`
  - `actions/setup-python@v5`
  - `actions/upload-artifact@v4`
- Verify Python 3.12+ within each workflow as shown in existing examples.

## Commit etiquette
- Keep commits focused and write clear messages detailing your reasoning.
- Remove temporary files and keep the repository tidy.
- Use an imperative, present-tense subject line ≤ 50 characters, followed by a blank line and a body wrapped at 72 characters.
- Reference related issue numbers.

Example commit message:

```
Update contribution guidelines

Explain commit message conventions and reference issue numbers
in the commit body. Closes #123.
```

## Legacy workflow
Autoresearch previously relied on **Poetry**, but `uv.lock` now tracks dependencies
and the old `poetry.lock` file has been removed. Use `uv venv` to create the
environment, `uv pip install -e '.[full,dev]'` to install dependencies, and `uv run <cmd>`
to invoke tools. Run `uv run pip install -e .` if you need an editable install.

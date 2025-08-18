# Contribution Guidelines

> Special note: before work begins, `scripts/codex_setup.sh` is executed to set up the environment. If it fails, a `CODEX_ENVIRONMENT_SETUP_FAILED` file will be created. If this marker is present, inspect `codex_setup.log` for details. This guide is the only document that may mention `scripts/codex_setup.sh`; do not reference it elsewhere.

Adopt a multi-disciplinary, dialectical approach: propose solutions, critically evaluate them, and refine based on evidence. Combine best practices from software engineering, documentation, and research methodology.

## Environment
- Keep `scripts/codex_setup.sh` in sync with these instructions; see the script for full setup, offline installs, and DuckDB extension options.
- Use Python 3.12+ and manage dependencies with `uv`; run all commands inside the virtual environment (`uv venv && uv sync --all-extras`).
- `VECTOR_EXTENSION_PATH` must point to `extensions/vss_stub.duckdb_extension` unless a real `vss.duckdb_extension` is available.
- Documents in `docs/inspirational_docs/` are inspirational only; cite external sources from `docs/external_research_papers/`.
- Remove build artifacts with `task clean` and delete temporary files such as `kg.duckdb` or `rdf_store`.

## Tooling
- Verify tooling within `.venv` (`task`, `flake8`, `pytest`, `mypy`, `pytest-bdd`, `pydantic`); rerun `scripts/codex_setup.sh` if any command is missing.
- Use `task` for common workflows; run `task verify` before committing and `task coverage` for explicit reports. See [Taskfile.yml](Taskfile.yml).
- Prefer `rg` for repository searches. If `task` is unavailable, use `uv run` equivalents for formatting, linting, type checking, and tests.
- Utility scripts live in [scripts/](scripts); run `task --list` or inspect the directory for more helpers.
- Dependencies are tracked in `uv.lock`; the previous `poetry.lock` is removed.
- Install dev extras with `uv pip install -e '.[full,parsers,git,llm,dev]'`; add `.[nlp]` for tests marked `requires_nlp` (see [tests/behavior/README.md](tests/behavior/README.md)).
- Requests to the `/metrics` endpoint must include an API key with the `metrics` permission.

## Workflow
- Place `AGENTS.md` in directories requiring custom instructions. Nested files override parent guidance.
- See [tests/AGENTS.md](tests/AGENTS.md) for test markers, extras, and cleanup.
- See [docs/AGENTS.md](docs/AGENTS.md) for documentation citations and formatting rules.
- Use the container’s clock for current dates and derive past dates from `git log`.
- Track work items in [`/issues`](issues); follow the rules in [issues/AGENTS.md](issues/AGENTS.md) and the template in [issues/README.md](issues/README.md).
- Avoid committing binary artifacts; the `extensions/` directory is placeholder only.
- GitHub Actions workflows must be dispatch-only, use `actions/checkout@v4`, `actions/setup-python@v5`, and `actions/upload-artifact@v4`, and verify Python 3.12+.
- Write focused commits with imperative subject lines ≤ 50 characters, wrap bodies at 72 characters, and reference related issues.

## Changelog
- 2025-08-18: Refer to `tests/AGENTS.md` and `docs/AGENTS.md` for scoped rules.
- Future updates to these instructions will be recorded here.

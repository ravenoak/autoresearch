# Address environment setup gaps for dev tooling

## Context
The prepared environment again misses key development tools. `task --version`
returns `command not found`, and `uv pip list | grep flake8` shows no result.
`which pytest` resolves to `/root/.pyenv/shims/pytest` instead of
`.venv/bin/pytest`. Running `uv run pytest -q` aborts with
`ModuleNotFoundError: pytest_httpx` before collecting tests. Attempting to install
development extras via `uv pip install -e '.[full,dev]'` triggers downloads of
hundreds of megabytes of GPU-related packages such as `torch` and
`nvidia-cudnn-cu12`, making setup impractical without prebuilt wheels. These
symptoms indicate the automated setup scripts and documentation have drifted
from the expected tooling.

Creating the virtual environment with `uv venv` and installing
`uv pip install -e '.[dev-minimal]'` now places `pytest`, `flake8`, and
`mypy` inside `.venv`, and `which pytest` resolves correctly. However,
Go Task remains unavailable and `ruff` is missing from the default
installation. Manual steps are also required to add `black` and `isort`.
Running linting reveals unresolved issues: `uv run ruff check --fix src
tests` reports `E402` in `src/autoresearch/visualization.py`, and
`uv run flake8 src tests` flags `E701` in `tests/stubs/a2a.py`.
Executing `uv run pytest tests/unit/test_cache.py::test_cache_lifecycle -q`
fails the coverage check (`fail-under=90`) even though the test passes.
Running the full suite still produces 181 failures, primarily
`TypeError` exceptions in Orchestrator-related integration tests, so
`task verify` remains broken.

## Acceptance Criteria
- Go Task is available after running the setup scripts.
- Development dependencies (e.g., `flake8`, `pytest-bdd`, `pytest-httpx`) install
  without manual steps.
- `task verify` runs successfully on a fresh environment.

## Status
Open

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
`uv pip install -e '.[dev-minimal]'` now places `pytest`, `flake8`, `mypy`, and
`ruff` inside `.venv`, and `which pytest` resolves correctly. However,
Go Task remains unavailable and manual steps are still required to add `black`
and `isort`. Running a targeted test such as
`uv run pytest tests/unit/test_cache.py::test_cache_lifecycle -q` succeeds but
fails the coverage check (`fail-under=90`). The full test suite continues to
produce hundreds of failures, primarily `TypeError` exceptions in
Orchestrator-related integration tests, so `task verify` remains broken.

After manually installing `pytest-bdd`, `pytest-httpx`, `pytest-cov`, and
`tomli_w`, the behavior test suite executes but fails at
`tests/behavior/steps/api_async_query_steps.py::test_async_query_result`
because the async status response lacks an "answer" field.

Subsequent test attempts surface additional `ModuleNotFoundError`
failures for runtime dependencies such as `uvicorn` and `psutil`.
The active environment also provides Python 3.11 even though project
documentation specifies Python 3.12 or newer, further complicating
setup.

## Acceptance Criteria
- Go Task is available after running the setup scripts.
- Development dependencies (e.g., `flake8`, `pytest-bdd`, `pytest-httpx`) install
  without manual steps.
- `task verify` runs successfully on a fresh environment.

## Status
Open

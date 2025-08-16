# Address environment setup gaps for dev tooling

## Context
The prepared environment again misses key development tools. `task --version`
returns `command not found`, and `uv pip list | grep flake8` shows no result.
Running `uv run pytest -q` initially fails with missing plugins such as
`pytest_httpx` and `pytest-bdd` until they are installed manually. Attempting to
use `uv sync --all-extras` pulls hundreds of megabytes of GPU related packages,
making setup impractical without prebuilt wheels. These symptoms indicate the
automated setup scripts and documentation have drifted from the expected
tooling.

## Acceptance Criteria
- Go Task is available after running the setup scripts.
- Development dependencies (e.g., `flake8`, `pytest-bdd`, `pytest-httpx`) install
  without manual steps.
- `task verify` runs successfully on a fresh environment.

## Status
Open

# Address environment setup gaps for dev tooling

## Context
Initial repository environment lacks the Go Task binary and development
packages like `flake8`, causing `task verify` to fail. Currently `which task`
prints nothing, `uv pip list | grep flake8` shows no result, and `uv run pytest
-q` aborts with `ModuleNotFoundError: typer`. Attempting to reinstall
dependencies with `uv pip install -e '.[full,parsers,git,llm,dev]'` begins
downloading hundreds of megabytes of CUDA-enabled packages, making setup
impractical without prebuilt wheels. Running `uv sync --all-extras` triggers the
same large downloads for GPU-backed libraries such as Torch and NVIDIA CUDA
components. The virtual environment also exposes
`pytest` via a pyenv shim instead of `.venv/bin/pytest`. These symptoms suggest
the automated setup scripts and documentation remain out of sync with the
expected tooling.

## Acceptance Criteria
- Go Task is available after running the provided setup scripts.
- Development dependencies (e.g., `flake8`) are installed without manual steps.
- `task verify` runs successfully on a fresh environment.

## Status
Open

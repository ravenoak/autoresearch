# Address environment setup gaps for dev tooling

## Context
Initial repository environment lacked the Go Task binary and development
packages like `flake8`, causing `task verify` to fail. Manual installation of
`task` and `uv pip install -e '.[full,parsers,git,llm,dev]'` was required before
linting and tests could run. This suggests the automated setup scripts or
documentation are out of sync with the expected tooling.

## Acceptance Criteria
- Go Task is available after running the provided setup scripts.
- Development dependencies (e.g., `flake8`) are installed without manual steps.
- `task verify` runs successfully on a fresh environment.

## Status
Open

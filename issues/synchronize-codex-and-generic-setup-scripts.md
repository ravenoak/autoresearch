# Synchronize Codex and generic setup scripts

## Context
`scripts/codex_setup.sh` installs development dependencies for Codex, while
`scripts/setup.sh` targets generic environments. Both call
`install_dev_test_extras` so the `dev` and `test` groups from
`pyproject.toml` stay aligned. The Codex helper additionally installs system
packages with `apt`, preloads models for offline tests, and verifies tools
like `flake8`, `mypy`, `responses`, `uvicorn`, `psutil`, and `a2a-sdk`. The
generic script checks `redis` and assumes OS libraries are present. Both
scripts explicitly install `pytest`, `pytest-bdd`, `freezegun`, and
`hypothesis` to satisfy the test suite. Missing parity previously left out
those packages, causing `task check` and `task verify` to fail on fresh
clones.

## Dependencies
- [document-task-cli-requirement](document-task-cli-requirement.md)
- [resolve-release-blockers-for-alpha](resolve-release-blockers-for-alpha.md)

## Acceptance Criteria
- `scripts/codex_setup.sh` and `scripts/setup.sh` both install `pytest`,
  `pytest-bdd`, `freezegun`, and `hypothesis`.
- `task check` runs without reinstalling removed test packages after either
  setup script.
- Documentation clarifies which script to use for Codex versus general
  contributors.
- Setup scripts finish within ten minutes.

## Status
Open

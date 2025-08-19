# Align environment with requirements

## Context
The project requires Python 3.12 and common development tools, but some
setups lag behind. The environment must match documented requirements to
avoid failures and missing tooling.

## Acceptance Criteria
- Python 3.12 is installed and selected as the default interpreter.
- Development tools such as task, flake8, mypy, pytest, pytest-bdd and
  pydantic are available in the virtual environment.

## 2025-08-19
- Python 3.12.10
- task 3.44.1
- flake8 7.3.0
- mypy 1.17.1
- pytest 8.4.1
- pytest-bdd 8.1.0
- pydantic 2.11.7

Verified that `uv venv && uv sync --all-extras` followed by
`uv pip install -e '.[full,parsers,git,llm,dev]'` installs these tools.

## Status
Archived

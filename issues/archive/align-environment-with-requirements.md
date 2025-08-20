# Align environment with requirements

## Context
The environment setup instructions still have gaps, leading to inconsistent developer installs.
Some systems miss Python 3.12 or required tooling, causing task failures and missing dependencies.
Recent setup with `uv sync --extra dev-minimal --extra test` succeeds, indicating dependencies are installable, but `uv run task verify` fails due to configuration command tests rather than missing packages.

## Acceptance Criteria
- Documented steps install Python 3.12 and all required development tools.
- `task install` completes on a clean machine without manual fixes.
- Environment checks verify versions align with project requirements.

## 2025-08-19
- Python 3.12.10
- task 3.44.1
- flake8 7.3.0
- mypy 1.17.1
- pytest 8.4.1
- pytest-bdd 8.1.0
- pydantic 2.11.7
Environment reverified and aligns with requirements.

## 2025-08-20
- Removed Python 3.11 shims and previous virtual environment.
- `task install` recreated environment with Python 3.12.10.
- `uv run python scripts/check_env.py` confirmed toolchain.
- `task verify` executed under Python 3.12.
Environment validated on clean setup.

## Status
Archived

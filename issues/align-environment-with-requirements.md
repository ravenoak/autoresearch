# Align environment with requirements

## Context
The environment setup instructions still have gaps, leading to inconsistent developer installs. Some
systems miss Python 3.12 or required tooling, causing task failures and missing dependencies.
Recent setup with `uv sync --extra dev-minimal --extra test` succeeds, indicating dependencies are
installable, but `uv run task verify` fails due to configuration command tests rather than missing
packages.

## Acceptance Criteria
- Documented steps install Python 3.12 and all required development tools.
- `task install` completes on a clean machine without manual fixes.
- Environment checks verify versions align with project requirements.

## Status
Open


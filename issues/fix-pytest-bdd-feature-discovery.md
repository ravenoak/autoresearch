# Fix pytest-bdd feature discovery

## Context
Running `uv run pytest tests/behavior/features/api_orchestrator_integration.feature -q`
reports `ERROR: not found: ... (no match in any of [<Dir features>])` because
`pytest-bdd` cannot discover the feature directory. Behavior tests cannot
execute reliably. This was reproduced on **August 24, 2025** after manually
installing `pytest-bdd`.

## Acceptance Criteria
- `uv run pytest tests/behavior/features/api_orchestrator_integration.feature -q`
  collects and runs the feature.
- Behavior tests run without manually configuring feature paths.
- Documentation reflects any required `pytest` configuration.

## Status
Open

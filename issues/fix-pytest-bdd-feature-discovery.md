# Fix pytest-bdd feature discovery

## Context
Running `uv run pytest tests/behavior/features/api_orchestrator_integration.feature -q`
reports `ERROR: not found: ... (no match in any of [<Dir features>])` because
`pytest-bdd` cannot discover the feature directory even with the plugin
installed. Behavior tests cannot execute reliably.

## Acceptance Criteria
- `uv run pytest tests/behavior/features/api_orchestrator_integration.feature -q`
  collects and runs the feature.
- Behavior tests run without manually configuring feature paths.
- Documentation reflects any required `pytest` configuration.

## Progress
- Imported missing step modules so pytest can load BDD scenarios.
- Directly running the feature still reports `not found`, indicating
  further path resolution is required.

## Status
Open

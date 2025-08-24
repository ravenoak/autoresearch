# Fix pytest-bdd feature discovery

## Context
Running `uv run pytest tests/integration/test_concurrent_queries.py \
 tests/behavior/features/api_orchestrator_integration.feature -q` fails
with "not found" because `pytest-bdd` cannot discover the feature
directory. Behavior tests cannot execute reliably.

## Acceptance Criteria
- `uv run pytest tests/behavior/features/api_orchestrator_integration.feature -q`
  collects and runs the feature.
- Behavior tests run without manually configuring feature paths.
- Documentation reflects any required `pytest` configuration.

## Status
Open

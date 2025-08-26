# Plan A2A MCP behavior tests

## Context
The A2A MCP integration needs behavior-driven tests to verify handshake
success, timeout handling, and recovery from errors. Breaking the effort into
smaller tasks will ease review and coordination.

## Acceptance Criteria
- Add a handshake success scenario in
  `tests/behavior/features/a2a_mcp_integration.feature`.
- Add a handshake timeout scenario in the same feature file.
- Add an error recovery scenario in the feature file.
- Implement step definitions for each scenario in
  `tests/behavior/steps/a2a_mcp_steps.py` and tag them with the
  `requires_distributed` marker for multi-agent coordination.
- Register `a2a_mcp` and `requires_distributed` markers in `pytest.ini`.
- Validate with `uv run pytest tests/behavior -m a2a_mcp -q`.

## Status
Open

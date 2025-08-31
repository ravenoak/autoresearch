# Test Tools

Helpers for exercising A2A and MCP endpoints.

## MCP client
- `MCPTestClient` checks connections and the research tool.

## A2A client
- `A2ATestClient` verifies connection, capabilities, and queries.

## Formatting
- `format_test_results` outputs JSON, plain text, or Markdown summaries.

## References
- [`test_tools.py`](../../src/autoresearch/test_tools.py)
- [../specs/test-tools.md](../specs/test-tools.md)

## Simulation

Automated tests confirm test tools behavior.

- [Spec](../specs/test-tools.md)
- [Tests](../../tests/unit/test_test_tools.py)

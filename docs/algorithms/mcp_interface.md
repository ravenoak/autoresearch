# MCP Interface

The MCP interface exposes the research tool over the FastMCP protocol. It
creates a server tool named `research` and accepts queries through client
calls.

## Protocol flow

- Server registers the `research` tool and listens for requests.
- Client connects and completes a handshake via `call_tool`.
- After the handshake, the query executes and returns the orchestrator's
  result.

## Security assumptions

- Transports may be local or remote; callers must be authorized.
- Timeouts guard against unresponsive or malicious clients.
- Errors propagate without leaking sensitive information.

## References

- [`mcp_interface.py`](../../src/autoresearch/mcp_interface.py)
- [`test_a2a_mcp_handshake.py`](../../tests/unit/test_a2a_mcp_handshake.py)

## Simulation

Automated tests confirm mcp interface behavior.

- [Spec](../specs/mcp-interface.md)
- [Tests](../../tests/unit/test_mcp_interface.py)
